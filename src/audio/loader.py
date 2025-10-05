"""
Audio file loading and validation
"""

import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AudioLoader:
    """Handles audio file loading and format conversion"""
    
    def __init__(self, target_sr: int = 16000):
        """
        Initialize audio loader
        
        Args:
            target_sr: Target sample rate for resampling
        """
        self.target_sr = target_sr
    
    def load(
        self,
        audio_path: Path,
        offset: float = 0.0,
        duration: Optional[float] = None
    ) -> Tuple[np.ndarray, int]:
        """
        Load audio file and resample to target sample rate
        
        Args:
            audio_path: Path to audio file
            offset: Start reading after this time (in seconds)
            duration: Only load this much audio (in seconds)
            
        Returns:
            Tuple of (audio_array, sample_rate)
        """
        try:
            # Load audio with librosa (handles multiple formats)
            audio, sr = librosa.load(
                audio_path,
                sr=self.target_sr,
                offset=offset,
                duration=duration,
                mono=True
            )
            
            logger.info(
                f"Loaded audio: {audio_path.name}, "
                f"duration={len(audio)/sr:.2f}s, sr={sr}Hz"
            )
            
            return audio, sr
            
        except Exception as e:
            logger.error(f"Failed to load audio {audio_path}: {e}")
            raise
    
    def save(
        self,
        audio: np.ndarray,
        output_path: Path,
        sample_rate: int
    ) -> None:
        """
        Save audio to file
        
        Args:
            audio: Audio array
            output_path: Output file path
            sample_rate: Sample rate
        """
        try:
            sf.write(output_path, audio, sample_rate)
            logger.info(f"Saved audio to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save audio to {output_path}: {e}")
            raise
    
    def get_duration(self, audio_path: Path) -> float:
        """
        Get audio duration without loading entire file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        try:
            duration = librosa.get_duration(path=audio_path)
            return duration
        except Exception as e:
            logger.error(f"Failed to get duration for {audio_path}: {e}")
            raise
    
    def validate_audio(
        self,
        audio_path: Path,
        max_duration_minutes: int = 120
    ) -> bool:
        """
        Validate audio file
        
        Args:
            audio_path: Path to audio file
            max_duration_minutes: Maximum allowed duration
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if file exists
            if not audio_path.exists():
                logger.error(f"Audio file does not exist: {audio_path}")
                return False
            
            # Check duration
            duration = self.get_duration(audio_path)
            max_duration_seconds = max_duration_minutes * 60
            
            if duration > max_duration_seconds:
                logger.error(
                    f"Audio too long: {duration:.2f}s > {max_duration_seconds}s"
                )
                return False
            
            if duration < 1.0:
                logger.error(f"Audio too short: {duration:.2f}s")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Audio validation failed: {e}")
            return False

