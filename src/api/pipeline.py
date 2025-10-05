"""
Main processing pipeline integrating all components
"""

from pathlib import Path
from typing import Optional, Dict, Any, Callable
import logging
from datetime import datetime

from src.config import settings
from src.audio import AudioLoader, AudioPreprocessor
from src.models import WhisperTranscriber, SpeakerDiarizer, EmotionDetector
from src.agents import AgentOrchestrator

logger = logging.getLogger(__name__)


class MeetingPipeline:
    """Integrated pipeline for meeting analysis"""
    
    def __init__(self):
        """Initialize pipeline components"""
        logger.info("Initializing Meeting Pipeline...")
        
        # Audio components
        self.audio_loader = AudioLoader(target_sr=settings.sample_rate)
        self.preprocessor = AudioPreprocessor(sample_rate=settings.sample_rate)
        
        # ML models
        self.transcriber = WhisperTranscriber(
            model_name=settings.whisper_model,
            device="auto"
        )
        
        self.diarizer = SpeakerDiarizer(
            model_name=settings.diarization_model,
            device="auto",
            hf_token=settings.huggingface_token
        )
        
        self.emotion_detector = EmotionDetector(
            model_name=settings.emotion_model,
            device="auto"
        )
        
        # Agent orchestrator
        self.orchestrator = AgentOrchestrator(
            llm_provider=settings.llm_provider,
            llm_model=settings.llm_model,
            llm_temperature=settings.llm_temperature,
            openai_api_key=settings.openai_api_key,
            google_api_key=settings.google_api_key,
            chroma_persist_dir=settings.chroma_persist_dir,
            enable_context_agent=True
        )
        
        logger.info("Meeting Pipeline initialized successfully")
    
    def process_meeting(
        self,
        audio_path: Path,
        num_speakers: Optional[int] = None,
        language: Optional[str] = None,
        enable_emotion: bool = True,
        enable_context: bool = True,
        task_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Dict[str, Any]:
        """
        Process meeting audio through complete pipeline
        
        Args:
            audio_path: Path to audio file
            num_speakers: Optional fixed number of speakers
            language: Optional language code
            enable_emotion: Enable emotion detection
            enable_context: Enable context verification
            task_id: Optional task ID for tracking
            progress_callback: Optional callback for progress updates
            
        Returns:
            Complete analysis results
        """
        logger.info(f"Processing meeting: {audio_path.name}")
        start_time = datetime.now()
        
        def update_progress(progress: int):
            if progress_callback:
                progress_callback(progress)
        
        try:
            # Step 1: Validate and load audio (10%)
            logger.info("Step 1: Loading and validating audio...")
            update_progress(5)
            
            if not self.audio_loader.validate_audio(
                audio_path,
                max_duration_minutes=settings.max_audio_length_minutes
            ):
                raise ValueError("Audio validation failed")
            
            audio, sr = self.audio_loader.load(audio_path)
            duration = len(audio) / sr
            update_progress(10)
            
            # Step 2: Preprocess audio (20%)
            logger.info("Step 2: Preprocessing audio...")
            audio = self.preprocessor.preprocess(audio)
            update_progress(20)
            
            # Step 3: Speaker diarization (35%)
            logger.info("Step 3: Performing speaker diarization...")
            diarization_segments = self.diarizer.diarize(
                audio_path,
                num_speakers=num_speakers
            )
            update_progress(35)
            
            # Step 4: Transcription (50%)
            logger.info("Step 4: Transcribing audio...")
            transcription = self.transcriber.transcribe(
                audio_path,
                return_timestamps=True
            )
            update_progress(50)
            
            # Step 5: Merge transcription with diarization (55%)
            logger.info("Step 5: Merging transcription with speakers...")
            segments = self.transcriber._merge_transcription_diarization(
                transcription["segments"],
                diarization_segments
            )
            update_progress(55)
            
            # Step 6: Emotion detection (70%)
            if enable_emotion:
                logger.info("Step 6: Detecting emotions...")
                segments = self.emotion_detector.detect_emotions_for_segments(
                    audio_path,
                    segments,
                    sample_rate=sr
                )
            update_progress(70)
            
            # Step 7: Multi-agent analysis (90%)
            logger.info("Step 7: Running multi-agent analysis...")
            meeting_data = {
                "segments": segments,
                "transcript": transcription["text"],
                "language": transcription["language"],
                "duration": duration,
                "audio_path": str(audio_path)
            }
            
            agent_results = self.orchestrator.process_meeting(
                meeting_data,
                meeting_id=task_id,
                store_context=enable_context
            )
            update_progress(90)
            
            # Step 8: Format final results (100%)
            logger.info("Step 8: Formatting results...")
            results = self._format_results(
                transcription=transcription,
                segments=segments,
                diarization_segments=diarization_segments,
                agent_results=agent_results,
                duration=duration,
                task_id=task_id
            )
            update_progress(100)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            results["processing_time_seconds"] = processing_time
            results["realtime_factor"] = processing_time / duration
            
            logger.info(
                f"Processing complete: {duration:.2f}s audio processed in "
                f"{processing_time:.2f}s (RTF: {results['realtime_factor']:.2f}x)"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}")
            raise
    
    def _format_results(
        self,
        transcription: Dict,
        segments: List[Dict],
        diarization_segments: List[Dict],
        agent_results: Dict,
        duration: float,
        task_id: Optional[str]
    ) -> Dict[str, Any]:
        """Format results into standardized response"""
        
        # Extract unique speakers
        speakers = sorted(list(set(seg["speaker"] for seg in segments)))
        
        # Build response
        results = {
            "meeting_id": task_id or datetime.now().strftime("%Y%m%d_%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "language": transcription["language"],
            "speakers": speakers,
            
            # Transcription
            "full_transcript": transcription["text"],
            "segments": segments,
            
            # Diarization stats
            "diarization_stats": {
                "num_segments": len(diarization_segments),
                "num_speakers": len(speakers),
                "speaker_times": self._calculate_speaker_times(segments)
            },
            
            # Actions and decisions
            "action_items": agent_results.get("actions", {}).get("action_items", []),
            "decisions": agent_results.get("actions", {}).get("decisions", []),
            "follow_ups": agent_results.get("actions", {}).get("follow_ups", []),
            "commitments": agent_results.get("actions", {}).get("commitments", []),
            
            # Sentiment
            "overall_sentiment": agent_results.get("sentiment", {}).get("overall_sentiment", {}),
            "speaker_sentiments": agent_results.get("sentiment", {}).get("speaker_sentiments", []),
            "emotional_shifts": agent_results.get("sentiment", {}).get("emotional_shifts", []),
            "meeting_dynamics": agent_results.get("sentiment", {}).get("meeting_dynamics", {}),
            
            # Context
            "context": agent_results.get("context"),
            
            # Executive summary
            "executive_summary": agent_results.get("executive_summary", {})
        }
        
        return results
    
    def _calculate_speaker_times(self, segments: List[Dict]) -> Dict[str, float]:
        """Calculate total speaking time per speaker"""
        speaker_times = {}
        
        for seg in segments:
            speaker = seg.get("speaker", "UNKNOWN")
            duration = seg.get("end", 0) - seg.get("start", 0)
            
            if speaker not in speaker_times:
                speaker_times[speaker] = 0.0
            
            speaker_times[speaker] += duration
        
        return speaker_times
    
    def cleanup(self):
        """Cleanup pipeline resources"""
        logger.info("Cleaning up pipeline resources...")
        self.transcriber.cleanup()
        self.diarizer.cleanup()
        self.emotion_detector.cleanup()

