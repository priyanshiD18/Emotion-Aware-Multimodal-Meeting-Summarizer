"""
Configuration management for the application
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")
    huggingface_token: str = Field(default="", env="HUGGINGFACE_TOKEN")
    
    # Weights & Biases
    wandb_api_key: str = Field(default="", env="WANDB_API_KEY")
    wandb_project: str = Field(default="meeting-intelligence", env="WANDB_PROJECT")
    wandb_entity: str = Field(default="", env="WANDB_ENTITY")
    
    # Model Configuration
    whisper_model: str = Field(default="large-v2", env="WHISPER_MODEL")
    diarization_model: str = Field(
        default="pyannote/speaker-diarization-3.1",
        env="DIARIZATION_MODEL"
    )
    emotion_model: str = Field(
        default="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
        env="EMOTION_MODEL"
    )
    
    # LLM Configuration
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4-turbo-preview", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.3, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")
    
    # Application Settings
    upload_dir: Path = Field(default=Path("./data/uploads"), env="UPLOAD_DIR")
    output_dir: Path = Field(default=Path("./data/outputs"), env="OUTPUT_DIR")
    cache_dir: Path = Field(default=Path("./models/cache"), env="CACHE_DIR")
    max_audio_length_minutes: int = Field(default=120, env="MAX_AUDIO_LENGTH_MINUTES")
    sample_rate: int = Field(default=16000, env="SAMPLE_RATE")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"],
        env="CORS_ORIGINS"
    )
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # ChromaDB
    chroma_persist_dir: Path = Field(
        default=Path("./data/chroma_db"),
        env="CHROMA_PERSIST_DIR"
    )
    
    class Config:
        env_file = "config.env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

