"""
Script to download and cache all required models
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.models import WhisperTranscriber, SpeakerDiarizer, EmotionDetector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_whisper_model():
    """Download WhisperX model"""
    logger.info("Downloading Whisper model...")
    try:
        transcriber = WhisperTranscriber(
            model_name=settings.whisper_model,
            device="cpu"
        )
        transcriber.load_model()
        logger.info("✅ Whisper model downloaded successfully")
        transcriber.cleanup()
    except Exception as e:
        logger.error(f"❌ Failed to download Whisper model: {e}")


def download_diarization_model():
    """Download Pyannote diarization model"""
    logger.info("Downloading diarization model...")
    try:
        diarizer = SpeakerDiarizer(
            model_name=settings.diarization_model,
            device="cpu",
            hf_token=settings.huggingface_token
        )
        diarizer.load_model()
        logger.info("✅ Diarization model downloaded successfully")
        diarizer.cleanup()
    except Exception as e:
        logger.error(f"❌ Failed to download diarization model: {e}")
        logger.info("Note: You need to accept the model license on HuggingFace and provide a token")


def download_emotion_model():
    """Download SpeechBrain emotion model"""
    logger.info("Downloading emotion detection model...")
    try:
        emotion_detector = EmotionDetector(
            model_name=settings.emotion_model,
            device="cpu"
        )
        emotion_detector.load_model()
        logger.info("✅ Emotion model downloaded successfully")
        emotion_detector.cleanup()
    except Exception as e:
        logger.error(f"❌ Failed to download emotion model: {e}")


def main():
    """Download all models"""
    logger.info("=" * 60)
    logger.info("Downloading all required models...")
    logger.info("=" * 60)
    
    # Check for required environment variables
    if not settings.huggingface_token:
        logger.warning("⚠️  HUGGINGFACE_TOKEN not set in config.env")
        logger.warning("Diarization model download may fail")
    
    download_whisper_model()
    print()
    
    download_diarization_model()
    print()
    
    download_emotion_model()
    print()
    
    logger.info("=" * 60)
    logger.info("Model download process complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

