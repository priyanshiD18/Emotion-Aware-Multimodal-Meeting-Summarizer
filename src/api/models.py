"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class TaskStatusEnum(str, Enum):
    """Task status enumeration"""
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    message: str
    timestamp: Optional[str] = None


class TaskStatus(BaseModel):
    """Task status response"""
    task_id: str
    status: TaskStatusEnum
    progress: int = Field(ge=0, le=100, description="Progress percentage")
    created_at: str
    updated_at: str
    error: Optional[str] = None


class SpeakerSegment(BaseModel):
    """Speaker segment with transcription and emotion"""
    start: float
    end: float
    speaker: str
    text: str
    emotion: Optional[str] = None
    emotion_confidence: Optional[float] = None


class ActionItem(BaseModel):
    """Action item extracted from meeting"""
    assignee: str
    task: str
    deadline: Optional[str] = None
    priority: str
    context: Optional[str] = None


class Decision(BaseModel):
    """Decision made in meeting"""
    decision: str
    decision_maker: str
    rationale: Optional[str] = None
    impact: Optional[str] = None


class SpeakerSentiment(BaseModel):
    """Sentiment analysis per speaker"""
    speaker: str
    dominant_emotion: str
    sentiment: str
    engagement_level: str
    communication_style: Optional[str] = None


class TranscriptionResponse(BaseModel):
    """Transcription-only response"""
    text: str
    segments: List[SpeakerSegment]
    language: str
    duration: float


class AnalysisResponse(BaseModel):
    """Complete analysis response"""
    meeting_id: str
    timestamp: str
    duration: float
    language: str
    speakers: List[str]
    
    # Transcription
    full_transcript: str
    segments: List[Dict[str, Any]]
    
    # Actions and decisions
    action_items: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]]
    follow_ups: List[Dict[str, Any]]
    
    # Sentiment
    overall_sentiment: Dict[str, Any]
    speaker_sentiments: List[Dict[str, Any]]
    emotional_shifts: List[Dict[str, Any]]
    
    # Context (optional)
    context: Optional[Dict[str, Any]] = None
    
    # Executive summary
    executive_summary: Dict[str, Any]


class UploadResponse(BaseModel):
    """File upload response"""
    file_id: str
    filename: str
    size_bytes: int
    status: str
    message: str

