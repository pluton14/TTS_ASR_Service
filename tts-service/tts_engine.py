"""TTS Engine implementation using gTTS (Google Text-to-Speech)."""

import asyncio
import io
import numpy as np
import soundfile as sf
import wave
import tempfile
import os
from typing import AsyncGenerator, Optional
from gtts import gTTS
from logger import get_logger
from config import settings

logger = get_logger(__name__)


class TTSEngine:
    """Text-to-Speech engine using gTTS (Google Text-to-Speech)."""
    
    def __init__(self):
        """Initialize TTS engine."""
        self.sample_rate = settings.sample_rate
        self.chunk_size = settings.chunk_size
        self.language = getattr(settings, 'tts_language', 'en')
        
        logger.info("TTS engine initialized", 
                   sample_rate=self.sample_rate,
                   chunk_size=self.chunk_size,
                   language=self.language)
    
    def is_healthy(self) -> bool:
        """Check if TTS engine is healthy."""
        try:
            # Simple health check - try to create a gTTS instance
            test_tts = gTTS(text="test", lang=self.language, slow=False)
            return True
        except Exception as e:
            logger.error("TTS engine health check failed", error=str(e))
            return False
    
    def _text_to_audio_bytes(self, text: str) -> bytes:
        """Convert text to audio bytes using gTTS."""
        try:
            logger.info("Converting text to speech", text_length=len(text))
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_filename = temp_file.name
            
            try:
                # Generate speech using gTTS
                tts = gTTS(text=text, lang=self.language, slow=False)
                tts.save(temp_filename)
                
                # Check if file was created and has content
                if not os.path.exists(temp_filename) or os.path.getsize(temp_filename) == 0:
                    logger.error("gTTS did not generate audio file")
                    return self._generate_simple_tone(text)
                
                # Read the generated audio file
                with open(temp_filename, "rb") as f:
                    audio_data = f.read()
                
                # Convert MP3 to WAV
                wav_data = self._convert_mp3_to_wav(audio_data)
                
                return wav_data
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_filename)
                except:
                    pass
            
        except Exception as e:
            logger.error("Failed to convert text to audio", error=str(e))
            logger.warning("Generating simple tone as fallback")
            return self._generate_simple_tone(text)
    
    def _convert_mp3_to_wav(self, mp3_data: bytes) -> bytes:
        """Convert MP3 data to WAV format."""
        try:
            from pydub import AudioSegment
            import io
            
            # Load MP3 from bytes
            audio_segment = AudioSegment.from_mp3(io.BytesIO(mp3_data))
            
            # Convert to mono and set sample rate
            audio_segment = audio_segment.set_channels(1)
            audio_segment = audio_segment.set_frame_rate(self.sample_rate)
            
            # Export as WAV
            wav_buffer = io.BytesIO()
            audio_segment.export(wav_buffer, format="wav")
            wav_buffer.seek(0)
            
            return wav_buffer.read()
            
        except Exception as e:
            logger.error("Failed to convert MP3 to WAV", error=str(e))
            # Fallback: generate simple tone
            return self._generate_simple_tone("conversion failed")
    
    def _generate_simple_tone(self, text: str) -> bytes:
        """Generate a simple audio tone as fallback."""
        try:
            # Calculate duration based on text length (rough estimate)
            duration = max(1.0, min(5.0, len(text) * 0.1))
            
            # Generate a more complex tone pattern
            t = np.linspace(0, duration, int(self.sample_rate * duration), False)
            
            # Create a more speech-like pattern with multiple frequencies
            frequency1 = 200  # Low frequency
            frequency2 = 400  # Mid frequency
            frequency3 = 800  # High frequency
            
            # Mix multiple sine waves with varying amplitudes
            wave_data = (
                0.3 * np.sin(2 * np.pi * frequency1 * t) +
                0.2 * np.sin(2 * np.pi * frequency2 * t) +
                0.1 * np.sin(2 * np.pi * frequency3 * t)
            )
            
            # Add some variation to make it less monotonous
            for i in range(0, len(wave_data), int(self.sample_rate * 0.3)):
                if i + int(self.sample_rate * 0.1) < len(wave_data):
                    # Add pauses
                    wave_data[i:i+int(self.sample_rate * 0.05)] *= 0.3
            
            # Convert to 16-bit PCM
            audio_data = (wave_data * 32767).astype(np.int16)
            
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            wav_buffer.seek(0)
            return wav_buffer.read()
            
        except Exception as e:
            logger.error("Failed to generate simple tone", error=str(e))
            # Ultimate fallback: generate silence
            duration = 2.0
            samples = int(self.sample_rate * duration)
            silence = np.zeros(samples, dtype=np.int16)
            
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(silence.tobytes())
            
            wav_buffer.seek(0)
            return wav_buffer.read()
    
    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """Generate audio stream from text."""
        try:
            logger.info("Starting TTS synthesis", text_length=len(text))
            
            # Convert text to audio bytes (already in WAV format)
            audio_bytes = self._text_to_audio_bytes(text)
            
            # Stream WAV data in chunks
            total_chunks = len(audio_bytes) // self.chunk_size
            remainder = len(audio_bytes) % self.chunk_size
            
            logger.info("Streaming audio chunks", 
                       total_chunks=total_chunks, 
                       chunk_size=self.chunk_size,
                       remainder=remainder)
            
            # Send chunks
            for i in range(total_chunks):
                start = i * self.chunk_size
                end = start + self.chunk_size
                chunk = audio_bytes[start:end]
                
                yield chunk
                
                # Small delay to simulate streaming
                await asyncio.sleep(0.01)
            
            # Send remainder if any
            if remainder > 0:
                start = total_chunks * self.chunk_size
                chunk = audio_bytes[start:]
                yield chunk
            
            logger.info("TTS synthesis completed")
            
        except Exception as e:
            logger.error("TTS synthesis failed", error=str(e))
            raise
    
    async def synthesize_stream_http(self, text: str) -> AsyncGenerator[bytes, None]:
        """Generate audio stream from text for HTTP endpoints."""
        async for chunk in self.synthesize_stream(text):
            yield chunk


# Global TTS engine instance
tts_engine = TTSEngine()