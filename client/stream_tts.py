#!/usr/bin/env python3
"""
Client script for testing TTS WebSocket streaming.
Connects to ws://localhost:8000/ws/tts, sends text, receives binary PCM frames,
and saves them to out.wav while printing timestamps.
"""

import asyncio
import json
import time
import wave
import websockets
from datetime import datetime
from typing import List


class TTSStreamClient:
    """Client for testing TTS WebSocket streaming."""
    
    def __init__(self, uri: str = "ws://localhost:8000/ws/tts"):
        self.uri = uri
        self.audio_chunks = []
        self.timestamps = []
    
    async def send_text_and_receive_audio(self, text: str):
        """Send text and receive audio stream."""
        print(f"Connecting to {self.uri}...")
        
        try:
            # Add timeout for connection
            async with websockets.connect(self.uri, timeout=10) as websocket:
                print(f"Connected! Sending text: '{text}'")
                
                # Send text message
                message = {"text": text}
                await websocket.send(json.dumps(message))
                print("Text sent, waiting for audio stream...")
                
                # Receive audio chunks with timeout
                start_time = time.time()
                chunk_count = 0
                last_chunk_time = time.time()
                
                try:
                    async for message in websocket:
                        if isinstance(message, bytes):
                            # Received audio chunk
                            current_time = time.time()
                            elapsed = current_time - start_time
                            last_chunk_time = current_time
                            
                            self.audio_chunks.append(message)
                            self.timestamps.append(elapsed)
                            chunk_count += 1
                            
                            print(f"Chunk {chunk_count}: {len(message)} bytes at {elapsed:.3f}s")
                            
                        elif isinstance(message, str):
                            try:
                                data = json.loads(message)
                                if data.get("type") == "end":
                                    print("Received end signal")
                                    break
                                elif "error" in data:
                                    print(f"Error: {data['error']}")
                                    break
                            except json.JSONDecodeError:
                                print(f"Received non-JSON text: {message}")
                        
                        # Timeout check - if no chunks for 10 seconds, break
                        if time.time() - last_chunk_time > 10:
                            print("Timeout: No audio chunks received for 10 seconds")
                            break
                
                except websockets.exceptions.ConnectionClosed:
                    print("WebSocket connection closed by server")
                
                total_time = time.time() - start_time
                print(f"\nStream completed in {total_time:.3f}s")
                print(f"Received {chunk_count} chunks, total size: {sum(len(chunk) for chunk in self.audio_chunks)} bytes")
                
        except asyncio.TimeoutError:
            print("Connection timeout")
        except Exception as e:
            print(f"Error: {e}")
            raise
    
    def save_audio_to_wav(self, filename: str = "out.wav", sample_rate: int = 22050):
        """Save received audio chunks to WAV file."""
        if not self.audio_chunks:
            print("No audio data to save")
            return
        
        print(f"Saving audio to {filename}...")
        
        # Combine all chunks
        audio_data = b''.join(self.audio_chunks)
        
        # Save as WAV file
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)
        
        print(f"Audio saved to {filename}")
        print(f"Duration: {len(audio_data) / (sample_rate * 2):.3f}s")
    
    def print_timestamps(self):
        """Print received chunk timestamps."""
        print("\nChunk timestamps:")
        for i, timestamp in enumerate(self.timestamps):
            print(f"  Chunk {i+1}: {timestamp:.3f}s")


async def main():
    """Main function."""
    print("=== TTS WebSocket Streaming Test ===")
    
    # Get text from user
    text = input("Enter text to synthesize (or press Enter for default): ").strip()
    if not text:
        text = "Hello world, this is a test of the streaming TTS service."
    
    print(f"Using text: '{text}'")
    
    # Create client and test
    client = TTSStreamClient()
    
    try:
        await client.send_text_and_receive_audio(text)
        client.save_audio_to_wav()
        client.print_timestamps()
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
