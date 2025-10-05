"""
Emotion detection from speech using SpeechBrain
"""

import torch
import torchaudio
from speechbrain.pretrained import EncoderClassifier
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import logging
import tempfile
import soundfile as sf

logger = logging.getLogger(__name__)


class EmotionDetector:
    """Handles emotion detection from speech using SpeechBrain"""
    
    # Emotion label mappings (IEMOCAP dataset)
    EMOTION_LABELS = {
        0: "neutral",
        1: "calm",
        2: "happy",
        3: "sad",
        4: "angry",
        5: "fearful",
        6: "disgust",
        7: "surprised"
    }
    
    def __init__(
        self,
        model_name: str = "speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
        device: str = "auto"
    ):
        """
        Initialize emotion detector
        
        Args:
            model_name: SpeechBrain model identifier
            device: Device to run on ("cuda", "cpu", or "auto")
        """
        self.model_name = model_name
        
        # Auto-detect device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(
            f"Initializing Emotion Detector: "
            f"model={model_name}, device={self.device}"
        )
        
        self.classifier = None
    
    def load_model(self) -> None:
        """Load emotion recognition model"""
        if self.classifier is None:
            logger.info("Loading emotion recognition model...")
            
            try:
                self.classifier = EncoderClassifier.from_hparams(
                    source=self.model_name,
                    run_opts={"device": self.device},
                    savedir=tempfile.mkdtemp()
                )
                logger.info("Emotion model loaded successfully")
                
            except Exception as e:
                logger.error(f"Failed to load emotion model: {e}")
                raise
    
    def detect_emotion(
        self,
        audio_path: Path
    ) -> Dict[str, float]:
        """
        Detect emotion from audio file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with emotion probabilities
        """
        self.load_model()
        
        try:
            # Get prediction
            out_prob, score, index, text_lab = self.classifier.classify_file(str(audio_path))
            
            # Convert to probabilities
            probs = torch.softmax(out_prob, dim=-1).squeeze().tolist()
            
            # Create emotion dict
            if isinstance(probs, float):
                probs = [probs]
            
            emotions = {}
            for i, prob in enumerate(probs):
                emotion_name = self.EMOTION_LABELS.get(i, f"emotion_{i}")
                emotions[emotion_name] = float(prob)
            
            # Get primary emotion
            primary_emotion = text_lab[0] if isinstance(text_lab, list) else str(text_lab)
            
            logger.debug(f"Detected emotion: {primary_emotion}")
            
            return {
                "primary_emotion": primary_emotion,
                "confidence": float(score.max()),
                "probabilities": emotions
            }
            
        except Exception as e:
            logger.error(f"Emotion detection failed for {audio_path}: {e}")
            return {
                "primary_emotion": "unknown",
                "confidence": 0.0,
                "probabilities": {}
            }
    
    def detect_emotion_from_array(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> Dict[str, float]:
        """
        Detect emotion from audio array
        
        Args:
            audio: Audio array
            sample_rate: Sample rate
            
        Returns:
            Dictionary with emotion probabilities
        """
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            sf.write(tmp_path, audio, sample_rate)
        
        try:
            result = self.detect_emotion(tmp_path)
            return result
        finally:
            # Cleanup
            tmp_path.unlink(missing_ok=True)
    
    def detect_emotions_for_segments(
        self,
        audio_path: Path,
        segments: List[Dict],
        sample_rate: int = 16000
    ) -> List[Dict]:
        """
        Detect emotions for each segment
        
        Args:
            audio_path: Path to full audio file
            segments: List of segments with start/end times
            sample_rate: Sample rate
            
        Returns:
            Segments with emotion annotations
        """
        self.load_model()
        
        logger.info(f"Detecting emotions for {len(segments)} segments")
        
        # Load full audio
        audio, sr = torchaudio.load(str(audio_path))
        
        # Resample if needed
        if sr != sample_rate:
            resampler = torchaudio.transforms.Resample(sr, sample_rate)
            audio = resampler(audio)
            sr = sample_rate
        
        # Convert to mono if needed
        if audio.shape[0] > 1:
            audio = torch.mean(audio, dim=0, keepdim=True)
        
        audio = audio.squeeze().numpy()
        
        # Process each segment
        annotated_segments = []
        for segment in segments:
            start_sample = int(segment["start"] * sr)
            end_sample = int(segment["end"] * sr)
            
            segment_audio = audio[start_sample:end_sample]
            
            # Detect emotion for segment
            emotion_result = self.detect_emotion_from_array(segment_audio, sr)
            
            # Add to segment
            annotated_segment = segment.copy()
            annotated_segment.update({
                "emotion": emotion_result["primary_emotion"],
                "emotion_confidence": emotion_result["confidence"],
                "emotion_probabilities": emotion_result["probabilities"]
            })
            
            annotated_segments.append(annotated_segment)
        
        logger.info("Emotion detection complete for all segments")
        return annotated_segments
    
    def get_dominant_emotions(
        self,
        segments: List[Dict],
        speaker: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get dominant emotions for a speaker or all speakers
        
        Args:
            segments: List of annotated segments
            speaker: Optional speaker to filter by
            
        Returns:
            Dictionary of emotion counts/percentages
        """
        # Filter by speaker if specified
        if speaker:
            segments = [s for s in segments if s.get("speaker") == speaker]
        
        if not segments:
            return {}
        
        # Count emotions
        emotion_counts = {}
        total_duration = 0
        
        for segment in segments:
            emotion = segment.get("emotion", "unknown")
            duration = segment.get("duration", segment.get("end", 0) - segment.get("start", 0))
            
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + duration
            total_duration += duration
        
        # Convert to percentages
        emotion_percentages = {
            emotion: (count / total_duration) * 100
            for emotion, count in emotion_counts.items()
        }
        
        return emotion_percentages
    
    def cleanup(self) -> None:
        """Free up memory"""
        if self.classifier is not None:
            del self.classifier
            self.classifier = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Emotion detector cleanup complete")

