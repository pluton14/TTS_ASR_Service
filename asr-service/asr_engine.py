
import io
import numpy as np
import soundfile as sf
import whisper
from typing import Optional, List, Tuple
from logger import get_logger
from config import settings
from models import ASRSegment

logger = get_logger(__name__)


class ASREngine:
    
    def __init__(self):
        self.model = None
        self.sample_rate = settings.sample_rate
        self.max_duration = settings.max_duration
        self.model_name = settings.model_name
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        try:
            logger.info("Loading Whisper model", model_name=self.model_name)
            
            self.model = whisper.load_model(self.model_name)
            
            logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            logger.error("Failed to load Whisper model", error=str(e))
            raise
    
    def _validate_audio(self, audio_data: np.ndarray, sample_rate: int) -> None:
        duration = len(audio_data) / sample_rate
        if duration > self.max_duration:
            raise ValueError(f"Audio duration ({duration:.2f}s) exceeds maximum allowed duration ({self.max_duration}s)")
        
        # Check if audio is not empty
        if len(audio_data) == 0:
            raise ValueError("Empty audio data")
        
        if np.max(np.abs(audio_data)) < 0.001:
            logger.warning("Audio level is very low")
    
    def _preprocess_audio(self, audio_bytes: bytes, sample_rate: int, channels: int) -> np.ndarray:
        try:
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Convert to float32 and normalize to [-1, 1]
            audio_data = audio_data.astype(np.float32) / 32768.0
            
            # Resample if necessary (no need since we're already at the correct sample rate)
            # The audio_data is already at the correct sample rate from the raw PCM
            
            # Normalize audio
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            return audio_data.astype(np.float32)
            
        except Exception as e:
            logger.error("Failed to preprocess audio", error=str(e))
            raise
    
    def _convert_segments(self, whisper_result: dict) -> List[ASRSegment]:
        segments = []
        
        if "segments" in whisper_result:
            for segment in whisper_result["segments"]:
                segments.append(ASRSegment(
                    start_ms=int(segment["start"] * 1000),
                    end_ms=int(segment["end"] * 1000),
                    text=segment["text"].strip()
                ))
        
        return segments
    
    def transcribe(self, audio_bytes: bytes, sample_rate: int, channels: int, language: str = "en") -> Tuple[str, List[ASRSegment]]:
        """Transcribe audio bytes to text."""
        try:
            logger.info("Starting transcription", 
                       audio_size=len(audio_bytes),
                       sample_rate=sample_rate,
                       channels=channels,
                       language=language)
            
            # Preprocess audio
            audio_data = self._preprocess_audio(audio_bytes, sample_rate, channels)
            
            # Validate audio
            self._validate_audio(audio_data, sample_rate)
            
            # Transcribe using Whisper
            result = self.model.transcribe(
                audio_data,
                language=language,
                verbose=False
            )
            
            # Extract text and segments
            text = result["text"].strip()
            segments = self._convert_segments(result)
            
            logger.info("Transcription completed", 
                       text_length=len(text),
                       segments_count=len(segments))
            
            return text, segments
            
        except Exception as e:
            logger.error("Transcription failed", error=str(e))
            raise
    
    def is_healthy(self) -> bool:
        """Check if ASR engine is healthy."""
        try:
            return self.model is not None
        except:
            return False


# Global ASR engine instance
asr_engine = ASREngine()
