"""
Tests for audio processing module
"""

import pytest
import numpy as np
from pathlib import Path

from src.audio import AudioLoader, AudioPreprocessor


class TestAudioLoader:
    """Test cases for AudioLoader"""
    
    def test_audio_loader_initialization(self):
        """Test AudioLoader initialization"""
        loader = AudioLoader(target_sr=16000)
        assert loader.target_sr == 16000
    
    def test_validate_audio_duration(self):
        """Test audio duration validation"""
        loader = AudioLoader(target_sr=16000)
        
        # Test with non-existent file
        assert not loader.validate_audio(
            Path("nonexistent.wav"),
            max_duration_minutes=10
        )


class TestAudioPreprocessor:
    """Test cases for AudioPreprocessor"""
    
    def test_preprocessor_initialization(self):
        """Test AudioPreprocessor initialization"""
        preprocessor = AudioPreprocessor(
            sample_rate=16000,
            apply_noise_reduction=True,
            apply_normalization=True
        )
        assert preprocessor.sample_rate == 16000
        assert preprocessor.apply_noise_reduction
        assert preprocessor.apply_normalization
    
    def test_normalize_audio(self):
        """Test audio normalization"""
        preprocessor = AudioPreprocessor(sample_rate=16000)
        
        # Create test audio
        audio = np.array([0.1, 0.5, -0.3, 0.8, -0.2])
        normalized = preprocessor.normalize(audio)
        
        # Check that max absolute value is 1.0
        assert np.abs(normalized).max() == pytest.approx(1.0)
    
    def test_segment_audio(self):
        """Test audio segmentation"""
        preprocessor = AudioPreprocessor(sample_rate=16000)
        
        # Create test audio (10 seconds)
        audio = np.random.randn(16000 * 10)
        
        # Segment into 3-second chunks with 1-second overlap
        segments = preprocessor.segment_audio(
            audio,
            segment_length=3.0,
            overlap=1.0
        )
        
        # Check that segments were created
        assert len(segments) > 0
        assert all(len(seg) > 0 for seg in segments)
    
    def test_extract_features(self):
        """Test feature extraction"""
        preprocessor = AudioPreprocessor(sample_rate=16000)
        
        # Create test audio
        audio = np.random.randn(16000)
        
        features = preprocessor.extract_features(audio)
        
        # Check that features are extracted
        assert "duration" in features
        assert "rms_energy" in features
        assert "zero_crossing_rate" in features
        assert features["duration"] == pytest.approx(1.0, rel=0.1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

