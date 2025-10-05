"""
Speaker diarization using Pyannote.audio
"""

from pyannote.audio import Pipeline
import torch
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SpeakerDiarizer:
    """Handles speaker diarization using Pyannote.audio"""
    
    def __init__(
        self,
        model_name: str = "pyannote/speaker-diarization-3.1",
        device: str = "auto",
        hf_token: Optional[str] = None
    ):
        """
        Initialize speaker diarizer
        
        Args:
            model_name: Pyannote model identifier
            device: Device to run on ("cuda", "cpu", or "auto")
            hf_token: HuggingFace authentication token
        """
        self.model_name = model_name
        self.hf_token = hf_token
        
        # Auto-detect device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(
            f"Initializing Pyannote Speaker Diarization: "
            f"model={model_name}, device={self.device}"
        )
        
        self.pipeline = None
    
    def load_model(self) -> None:
        """Load diarization pipeline"""
        if self.pipeline is None:
            logger.info("Loading diarization pipeline...")
            
            try:
                self.pipeline = Pipeline.from_pretrained(
                    self.model_name,
                    use_auth_token=self.hf_token
                )
                
                # Move to device
                if self.device == "cuda":
                    self.pipeline = self.pipeline.to(torch.device("cuda"))
                
                logger.info("Diarization pipeline loaded successfully")
                
            except Exception as e:
                logger.error(f"Failed to load diarization pipeline: {e}")
                logger.info("Please ensure you have accepted the model license and provided HF token")
                raise
    
    def diarize(
        self,
        audio_path: Path,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> List[Dict]:
        """
        Perform speaker diarization
        
        Args:
            audio_path: Path to audio file
            num_speakers: Fixed number of speakers (if known)
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers
            
        Returns:
            List of diarization segments with speaker labels
        """
        self.load_model()
        
        logger.info(f"Diarizing: {audio_path.name}")
        
        # Prepare diarization parameters
        diarization_params = {}
        if num_speakers is not None:
            diarization_params["num_speakers"] = num_speakers
        else:
            if min_speakers is not None:
                diarization_params["min_speakers"] = min_speakers
            if max_speakers is not None:
                diarization_params["max_speakers"] = max_speakers
        
        # Run diarization
        diarization = self.pipeline(str(audio_path), **diarization_params)
        
        # Convert to list of segments
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker,
                "duration": turn.end - turn.start
            })
        
        # Get speaker statistics
        speakers = set(seg["speaker"] for seg in segments)
        
        logger.info(
            f"Diarization complete: {len(segments)} segments, "
            f"{len(speakers)} speakers detected"
        )
        
        return segments
    
    def get_speaker_statistics(self, segments: List[Dict]) -> Dict:
        """
        Calculate speaker statistics
        
        Args:
            segments: List of diarization segments
            
        Returns:
            Dictionary of speaker statistics
        """
        stats = {}
        
        for segment in segments:
            speaker = segment["speaker"]
            duration = segment["duration"]
            
            if speaker not in stats:
                stats[speaker] = {
                    "total_duration": 0.0,
                    "num_segments": 0,
                    "avg_segment_length": 0.0
                }
            
            stats[speaker]["total_duration"] += duration
            stats[speaker]["num_segments"] += 1
        
        # Calculate averages
        for speaker in stats:
            stats[speaker]["avg_segment_length"] = (
                stats[speaker]["total_duration"] / stats[speaker]["num_segments"]
            )
        
        return stats
    
    def merge_short_segments(
        self,
        segments: List[Dict],
        min_duration: float = 1.0
    ) -> List[Dict]:
        """
        Merge very short segments with adjacent segments
        
        Args:
            segments: List of diarization segments
            min_duration: Minimum segment duration in seconds
            
        Returns:
            List of merged segments
        """
        if not segments:
            return segments
        
        merged = []
        current_segment = segments[0].copy()
        
        for next_segment in segments[1:]:
            # If current segment is too short and same speaker
            if (current_segment["duration"] < min_duration and
                current_segment["speaker"] == next_segment["speaker"]):
                # Merge segments
                current_segment["end"] = next_segment["end"]
                current_segment["duration"] = (
                    current_segment["end"] - current_segment["start"]
                )
            else:
                merged.append(current_segment)
                current_segment = next_segment.copy()
        
        merged.append(current_segment)
        
        logger.info(f"Merged segments: {len(segments)} -> {len(merged)}")
        return merged
    
    def cleanup(self) -> None:
        """Free up memory"""
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Diarization cleanup complete")

