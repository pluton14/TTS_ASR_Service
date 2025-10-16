#!/usr/bin/env python3
"""
Client script for testing echo-bytes functionality.
Reads input.wav, converts to PCM bytes, sends to POST /api/echo-bytes,
and saves the incoming chunked stream to out_echo.wav.
"""

import asyncio
import httpx
import wave
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Optional


class EchoBytesClient:
    """Client for testing echo-bytes functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    def load_audio_file(self, filename: str) -> tuple[np.ndarray, int]:
        """Load audio file and return data with sample rate."""
        file_path = Path(filename)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {filename}")
        
        print(f"Loading audio file: {filename}")
        
        # Load audio file
        data, sample_rate = sf.read(str(file_path))
        
        # Convert to mono if stereo
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
            print("Converted stereo to mono")
        
        print(f"Audio loaded: {len(data)} samples, {sample_rate} Hz, {len(data)/sample_rate:.3f}s")
        
        return data, sample_rate
    
    def audio_to_pcm_bytes(self, audio_data: np.ndarray, sample_rate: int) -> bytes:
        """Convert audio data to PCM bytes."""
        # Normalize to [-1, 1] if needed
        if np.max(np.abs(audio_data)) > 1.0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        # Convert to 16-bit PCM
        pcm_data = (audio_data * 32767).astype(np.int16)
        
        # Convert to bytes
        pcm_bytes = pcm_data.tobytes()
        
        print(f"Converted to PCM: {len(pcm_bytes)} bytes")
        
        return pcm_bytes
    
    async def send_echo_request(self, pcm_bytes: bytes, sample_rate: int, channels: int = 1) -> bytes:
        """Send echo-bytes request and return received audio."""
        url = f"{self.base_url}/api/echo-bytes"
        params = {
            "sr": sample_rate,
            "ch": channels,
            "fmt": "s16le"
        }
        
        print(f"Sending echo request to {url}")
        print(f"Parameters: {params}")
        
        try:
            response = await self.client.post(
                url,
                params=params,
                content=pcm_bytes,
                headers={"Content-Type": "application/octet-stream"}
            )
            response.raise_for_status()
            
            # Read the streaming response
            echo_audio = b""
            async for chunk in response.aiter_bytes():
                echo_audio += chunk
            
            print(f"Received echo audio: {len(echo_audio)} bytes")
            
            return echo_audio
            
        except Exception as e:
            print(f"Echo request failed: {e}")
            raise
    
    def save_echo_audio(self, echo_audio: bytes, filename: str, sample_rate: int):
        """Save echo audio to WAV file."""
        print(f"Saving echo audio to {filename}...")
        
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(echo_audio)
        
        duration = len(echo_audio) / (sample_rate * 2)
        print(f"Echo audio saved: {duration:.3f}s")
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


def create_test_audio(filename: str = "input.wav", duration: float = 3.0, sample_rate: int = 16000):
    """Create a test audio file with a simple tone."""
    print(f"Creating test audio file: {filename}")
    
    # Generate a simple sine wave
    frequency = 440  # A4 note
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    # Add some variation to make it more interesting for ASR
    audio_data += 0.1 * np.sin(2 * np.pi * frequency * 2 * t)
    
    # Save as WAV file
    sf.write(filename, audio_data, sample_rate)
    
    print(f"Test audio created: {duration}s, {sample_rate} Hz")


async def main():
    """Main function."""
    print("=== Echo Bytes Test ===")
    
    input_file = "input.wav"
    output_file = "out_echo.wav"
    
    # Check if input file exists, create one if not
    if not Path(input_file).exists():
        print(f"Input file {input_file} not found. Creating test audio...")
        create_test_audio(input_file)
        print("Note: This is just a test tone. For real speech recognition, provide an actual speech file.")
    
    client = EchoBytesClient()
    
    try:
        # Load input audio
        audio_data, sample_rate = client.load_audio_file(input_file)
        
        # Convert to PCM bytes
        pcm_bytes = client.audio_to_pcm_bytes(audio_data, sample_rate)
        
        # Send echo request
        echo_audio = await client.send_echo_request(pcm_bytes, sample_rate)
        
        # Save echo audio
        client.save_echo_audio(echo_audio, output_file, sample_rate)
        
        print("\nEcho bytes test completed successfully!")
        print(f"Input: {input_file}")
        print(f"Output: {output_file}")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
