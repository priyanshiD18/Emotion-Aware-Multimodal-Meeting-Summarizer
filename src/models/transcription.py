"""
Speech-to-text transcription using WhisperX
"""

import whisperx
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import logging
import gc

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Handles speech-to-text transcription using WhisperX"""
    
    def __init__(
        self,
        model_name: str = "large-v2",
        device: str = "auto",
        compute_type: str = "float16",
        language: Optional[str] = None
    ):
        """
        Initialize WhisperX transcriber
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large-v2, large-v3)
            device: Device to run on ("cuda", "cpu", or "auto")
            compute_type: Computation precision ("float16", "int8", "float32")
            language: Force language (None for auto-detection)
        """
        self.model_name = model_name
        self.language = language
        
        # Auto-detect device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        # Adjust compute type based on device
        if self.device == "cpu":
            self.compute_type = "int8"
        else:
            self.compute_type = compute_type
        
        logger.info(
            f"Initializing WhisperX: model={model_name}, "
            f"device={self.device}, compute_type={self.compute_type}"
        )
        
        self.model = None
        self.align_model = None
        self.align_metadata = None
    
    def load_model(self) -> None:
        """Load Whisper model"""
        if self.model is None:
            logger.info("Loading Whisper model...")
            self.model = whisperx.load_model(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type
            )
            logger.info("Whisper model loaded successfully")
    
    def transcribe(
        self,
        audio_path: Path,
        batch_size: int = 16,
        return_timestamps: bool = True
    ) -> Dict:
        """
        Transcribe audio file
        
        Args:
            audio_path: Path to audio file
            batch_size: Batch size for inference
            return_timestamps: Whether to return word-level timestamps
            
        Returns:
            Dictionary with transcription results
        """
        self.load_model()
        
        logger.info(f"Transcribing: {audio_path.name}")
        
        # Load audio
        audio = whisperx.load_audio(str(audio_path))
        
        # Transcribe
        result = self.model.transcribe(
            audio,
            batch_size=batch_size,
            language=self.language
        )
        
        # Align timestamps
        if return_timestamps and result.get("segments"):
            result = self.align_timestamps(audio, result)
        
        # Extract language if auto-detected
        detected_language = result.get("language", "unknown")
        
        logger.info(
            f"Transcription complete: {len(result.get('segments', []))} segments, "
            f"language={detected_language}"
        )
        
        return {
            "text": result.get("text", ""),
            "segments": result.get("segments", []),
            "language": detected_language,
            "word_segments": result.get("word_segments", [])
        }
    
    def align_timestamps(self, audio: np.ndarray, transcription: Dict) -> Dict:
        """
        Align timestamps using WhisperX alignment model
        
        Args:
            audio: Audio array
            transcription: Initial transcription results
            
        Returns:
            Transcription with aligned timestamps
        """
        try:
            # Load alignment model if not already loaded
            if self.align_model is None:
                detected_language = transcription.get("language", "en")
                logger.info(f"Loading alignment model for language: {detected_language}")
                
                self.align_model, self.align_metadata = whisperx.load_align_model(
                    language_code=detected_language,
                    device=self.device
                )
            
            # Align
            result = whisperx.align(
                transcription["segments"],
                self.align_model,
                self.align_metadata,
                audio,
                self.device,
                return_char_alignments=False
            )
            
            logger.debug("Timestamp alignment complete")
            return result
            
        except Exception as e:
            logger.warning(f"Timestamp alignment failed: {e}")
            return transcription
    
    def transcribe_with_diarization(
        self,
        audio_path: Path,
        diarization_result: Dict,
        batch_size: int = 16
    ) -> List[Dict]:
        """
        Transcribe and assign speakers using diarization results
        
        Args:
            audio_path: Path to audio file
            diarization_result: Speaker diarization results
            batch_size: Batch size for inference
            
        Returns:
            List of segments with speaker labels and transcriptions
        """
        # Get transcription
        transcription = self.transcribe(audio_path, batch_size)
        
        # Merge with diarization
        segments = self._merge_transcription_diarization(
            transcription["segments"],
            diarization_result
        )
        
        return segments
    
    def _merge_transcription_diarization(
        self,
        transcription_segments: List[Dict],
        diarization_segments: List[Dict]
    ) -> List[Dict]:
        """
        Merge transcription and diarization results
        
        Args:
            transcription_segments: Segments from transcription
            diarization_segments: Segments from diarization
            
        Returns:
            Merged segments with speaker labels
        """
        merged_segments = []
        
        for trans_seg in transcription_segments:
            trans_start = trans_seg["start"]
            trans_end = trans_seg["end"]
            trans_mid = (trans_start + trans_end) / 2
            
            # Find overlapping speaker
            speaker = "UNKNOWN"
            max_overlap = 0
            
            for dia_seg in diarization_segments:
                dia_start = dia_seg["start"]
                dia_end = dia_seg["end"]
                
                # Calculate overlap
                overlap_start = max(trans_start, dia_start)
                overlap_end = min(trans_end, dia_end)
                overlap = max(0, overlap_end - overlap_start)
                
                if overlap > max_overlap:
                    max_overlap = overlap
                    speaker = dia_seg["speaker"]
            
            merged_segments.append({
                "start": trans_start,
                "end": trans_end,
                "text": trans_seg["text"],
                "speaker": speaker
            })
        
        return merged_segments
    
    def cleanup(self) -> None:
        """Free up memory"""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.align_model is not None:
            del self.align_model
            self.align_model = None
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("WhisperX cleanup complete")

