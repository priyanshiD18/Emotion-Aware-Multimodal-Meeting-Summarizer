"""
FastAPI application entry point
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Optional
import logging
from datetime import datetime
import uuid

from src.config import settings
from .models import (
    TranscriptionResponse,
    AnalysisResponse,
    TaskStatus,
    HealthResponse
)
from .pipeline import MeetingPipeline
from .tasks import TaskManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Meeting Intelligence API",
    description="AI-powered meeting transcription, diarization, and analysis",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline and task manager
pipeline = MeetingPipeline()
task_manager = TaskManager()


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    logger.info("Starting Meeting Intelligence API...")
    logger.info(f"Upload directory: {settings.upload_dir}")
    logger.info(f"Output directory: {settings.output_dir}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down Meeting Intelligence API...")
    pipeline.cleanup()


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        message="Meeting Intelligence API is running"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        message="All systems operational",
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/v1/upload")
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload audio file for processing
    
    Args:
        file: Audio file (wav, mp3, m4a, etc.)
        
    Returns:
        Upload confirmation with file ID
    """
    try:
        # Validate file type
        allowed_extensions = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. "
                       f"Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        file_path = settings.upload_dir / f"{file_id}{file_ext}"
        
        # Save file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"Uploaded file: {file.filename} -> {file_id}")
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "size_bytes": len(contents),
            "status": "uploaded",
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyze", response_model=dict)
async def analyze_meeting(
    file_id: str,
    background_tasks: BackgroundTasks,
    num_speakers: Optional[int] = None,
    language: Optional[str] = None,
    enable_emotion: bool = True,
    enable_context: bool = True
):
    """
    Analyze uploaded meeting audio
    
    Args:
        file_id: File ID from upload endpoint
        background_tasks: FastAPI background tasks
        num_speakers: Optional fixed number of speakers
        language: Optional language code (auto-detect if None)
        enable_emotion: Whether to enable emotion detection
        enable_context: Whether to enable context verification
        
    Returns:
        Task ID for tracking analysis progress
    """
    try:
        # Find uploaded file
        matching_files = list(settings.upload_dir.glob(f"{file_id}.*"))
        if not matching_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        audio_path = matching_files[0]
        
        # Create task
        task_id = task_manager.create_task(file_id)
        
        # Process in background
        background_tasks.add_task(
            process_meeting_task,
            task_id=task_id,
            audio_path=audio_path,
            num_speakers=num_speakers,
            language=language,
            enable_emotion=enable_emotion,
            enable_context=enable_context
        )
        
        logger.info(f"Started analysis task: {task_id}")
        
        return {
            "task_id": task_id,
            "file_id": file_id,
            "status": "processing",
            "message": "Analysis started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get status of analysis task
    
    Args:
        task_id: Task ID from analyze endpoint
        
    Returns:
        Task status information
    """
    status = task_manager.get_status(task_id)
    
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return status


@app.get("/api/v1/result/{task_id}", response_model=AnalysisResponse)
async def get_analysis_result(task_id: str):
    """
    Get analysis results for completed task
    
    Args:
        task_id: Task ID from analyze endpoint
        
    Returns:
        Complete analysis results
    """
    result = task_manager.get_result(task_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    
    if result.get("status") == "failed":
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Analysis failed")
        )
    
    return result


async def process_meeting_task(
    task_id: str,
    audio_path: Path,
    num_speakers: Optional[int],
    language: Optional[str],
    enable_emotion: bool,
    enable_context: bool
):
    """
    Background task for processing meeting
    
    Args:
        task_id: Task ID
        audio_path: Path to audio file
        num_speakers: Optional number of speakers
        language: Optional language code
        enable_emotion: Enable emotion detection
        enable_context: Enable context verification
    """
    try:
        # Update status
        task_manager.update_status(task_id, "processing", progress=0)
        
        # Process meeting
        result = pipeline.process_meeting(
            audio_path=audio_path,
            num_speakers=num_speakers,
            language=language,
            enable_emotion=enable_emotion,
            enable_context=enable_context,
            task_id=task_id,
            progress_callback=lambda p: task_manager.update_status(
                task_id, "processing", progress=p
            )
        )
        
        # Save result
        task_manager.save_result(task_id, result)
        task_manager.update_status(task_id, "completed", progress=100)
        
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        task_manager.update_status(task_id, "failed", error=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

