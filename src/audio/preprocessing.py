"""
Audio preprocessing: noise reduction, normalization, VAD
"""

import numpy as np
import librosa
import noisereduce as nr
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AudioPreprocessor:
    """Handles audio preprocessing operations"""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        apply_noise_reduction: bool = True,
        apply_normalization: bool = True
    ):
        """
        Initialize audio preprocessor
        
        Args:
            sample_rate: Audio sample rate
            apply_noise_reduction: Whether to apply noise reduction
            apply_normalization: Whether to normalize audio
        """
        self.sample_rate = sample_rate
        self.apply_noise_reduction = apply_noise_reduction
        self.apply_normalization = apply_normalization
    
    def preprocess(
        self,
        audio: np.ndarray,
        noise_profile: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Apply full preprocessing pipeline
        
        Args:
            audio: Input audio array
            noise_profile: Optional noise profile for noise reduction
            
        Returns:
            Preprocessed audio array
        """
        processed_audio = audio.copy()
        
        # Noise reduction
        if self.apply_noise_reduction:
            processed_audio = self.reduce_noise(processed_audio, noise_profile)
        
        # Normalization
        if self.apply_normalization:
            processed_audio = self.normalize(processed_audio)
        
        # Remove silence
        processed_audio = self.trim_silence(processed_audio)
        
        logger.info("Audio preprocessing complete")
        return processed_audio
    
    def reduce_noise(
        self,
        audio: np.ndarray,
        noise_profile: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Apply noise reduction
        
        Args:
            audio: Input audio array
            noise_profile: Optional noise sample for stationary noise
            
        Returns:
            Denoised audio
        """
        try:
            if noise_profile is not None:
                # Use provided noise profile
                reduced_noise = nr.reduce_noise(
                    y=audio,
                    sr=self.sample_rate,
                    y_noise=noise_profile,
                    stationary=True
                )
            else:
                # Auto-detect and reduce noise
                reduced_noise = nr.reduce_noise(
                    y=audio,
                    sr=self.sample_rate,
                    stationary=False
                )
            
            logger.debug("Noise reduction applied")
            return reduced_noise
            
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}, returning original audio")
            return audio
    
    def normalize(self, audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio to [-1, 1] range
        
        Args:
            audio: Input audio array
            
        Returns:
            Normalized audio
        """
        max_val = np.abs(audio).max()
        if max_val > 0:
            normalized = audio / max_val
            logger.debug("Audio normalized")
            return normalized
        return audio
    
    def trim_silence(
        self,
        audio: np.ndarray,
        top_db: int = 30
    ) -> np.ndarray:
        """
        Remove leading and trailing silence
        
        Args:
            audio: Input audio array
            top_db: Threshold in dB below reference to consider silence
            
        Returns:
            Trimmed audio
        """
        trimmed, _ = librosa.effects.trim(audio, top_db=top_db)
        logger.debug("Silence trimmed")
        return trimmed
    
    def apply_preemphasis(
        self,
        audio: np.ndarray,
        coef: float = 0.97
    ) -> np.ndarray:
        """
        Apply pre-emphasis filter to enhance high frequencies
        
        Args:
            audio: Input audio array
            coef: Pre-emphasis coefficient
            
        Returns:
            Pre-emphasized audio
        """
        emphasized = np.append(audio[0], audio[1:] - coef * audio[:-1])
        return emphasized
    
    def segment_audio(
        self,
        audio: np.ndarray,
        segment_length: float = 30.0,
        overlap: float = 5.0
    ) -> list:
        """
        Segment audio into overlapping chunks
        
        Args:
            audio: Input audio array
            segment_length: Length of each segment in seconds
            overlap: Overlap between segments in seconds
            
        Returns:
            List of audio segments
        """
        segment_samples = int(segment_length * self.sample_rate)
        overlap_samples = int(overlap * self.sample_rate)
        stride = segment_samples - overlap_samples
        
        segments = []
        for start in range(0, len(audio) - segment_samples + 1, stride):
            end = start + segment_samples
            segments.append(audio[start:end])
        
        # Add final segment if remaining audio
        if len(audio) % stride != 0:
            segments.append(audio[-segment_samples:])
        
        logger.info(f"Audio segmented into {len(segments)} chunks")
        return segments
    
    def extract_features(self, audio: np.ndarray) -> dict:
        """
        Extract audio features for analysis
        
        Args:
            audio: Input audio array
            
        Returns:
            Dictionary of audio features
        """
        features = {
            "duration": len(audio) / self.sample_rate,
            "rms_energy": float(np.sqrt(np.mean(audio**2))),
            "zero_crossing_rate": float(np.mean(librosa.zero_crossings(audio))),
            "spectral_centroid": float(
                np.mean(librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate))
            ),
            "spectral_rolloff": float(
                np.mean(librosa.feature.spectral_rolloff(y=audio, sr=self.sample_rate))
            ),
        }
        
        return features

