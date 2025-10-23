
import asyncio
import json
import httpx
import websockets
from typing import AsyncGenerator, Dict, Any, Optional
from logger import get_logger
from config import settings

logger = get_logger(__name__)


class TTSServiceClient:
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def synthesize_stream_http(self, text: str) -> AsyncGenerator[bytes, None]:
        try:
            url = f"{self.base_url}/api/tts"
            payload = {"text": text}
            
            logger.info("Starting HTTP TTS request", text_length=len(text))
            
            async with self.http_client.stream(
                "POST", 
                url, 
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                
                async for chunk in response.aiter_bytes():
                    yield chunk
            
            logger.info("HTTP TTS request completed")
            
        except Exception as e:
            logger.error("HTTP TTS request failed", error=str(e))
            raise
    
    async def synthesize_stream_websocket(self, websocket, text: str) -> None:
        try:
            tts_ws_url = f"{self.base_url.replace('http', 'ws')}/ws/tts"
            
            logger.info("Connecting to TTS WebSocket", url=tts_ws_url)
            
            async with websockets.connect(tts_ws_url) as tts_websocket:
                # Send text to TTS service
                message = {"text": text}
                await tts_websocket.send(json.dumps(message))
                
                # Stream audio chunks to client
                async for message in tts_websocket:
                    if isinstance(message, bytes):
                        # Forward audio chunk to client
                        await websocket.send_bytes(message)
                    elif isinstance(message, str):
                        try:
                            data = json.loads(message)
                            if data.get("type") == "end":
                                # Forward end message to client
                                await websocket.send_text(json.dumps({"type": "end"}))
                                break
                        except json.JSONDecodeError:
                            logger.warning("Received non-JSON text message from TTS", message=message)
            
            logger.info("WebSocket TTS request completed")
            
        except Exception as e:
            logger.error("WebSocket TTS request failed", error=str(e))
            raise
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()


class ASRServiceClient:
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def transcribe(self, audio_bytes: bytes, sample_rate: int, channels: int, language: str = "en") -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/api/stt/bytes"
            params = {
                "sr": sample_rate,
                "ch": channels,
                "lang": language,
                "fmt": "s16le"
            }
            
            logger.info("Starting ASR request", 
                       audio_size=len(audio_bytes),
                       sample_rate=sample_rate,
                       channels=channels)
            
            response = await self.http_client.post(
                url,
                params=params,
                content=audio_bytes,
                headers={"Content-Type": "application/octet-stream"}
            )
            
            logger.info("ASR response received", 
                       status_code=response.status_code,
                       content_type=response.headers.get("content-type", "unknown"))
            
            if response.status_code != 200:
                logger.error("ASR request failed", 
                           status_code=response.status_code,
                           response_text=response.text)
                response.raise_for_status()
            
            result = response.json()
            
            logger.info("ASR request completed", 
                       text_length=len(result.get("text", "")),
                       segments_count=len(result.get("segments", [])),
                       result=result)
            
            return result
            
        except Exception as e:
            logger.error("ASR request failed", error=str(e))
            raise
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()


class ServiceManager:
    
    def __init__(self):
        self.tts_client = TTSServiceClient(settings.tts_service_url)
        self.asr_client = ASRServiceClient(settings.asr_service_url)
    
    async def check_services_health(self) -> Dict[str, bool]:
        """Check health of all services."""
        health_status = {}
        
        try:
            # Check TTS service
            tts_response = await self.tts_client.http_client.get(f"{settings.tts_service_url}/health")
            health_status["tts"] = tts_response.status_code == 200
        except:
            health_status["tts"] = False
        
        try:
            # Check ASR service
            asr_response = await self.asr_client.http_client.get(f"{settings.asr_service_url}/health")
            health_status["asr"] = asr_response.status_code == 200
        except:
            health_status["asr"] = False
        
        return health_status
    
    async def close(self):
        await self.tts_client.close()
        await self.asr_client.close()


# Global service manager instance
service_manager = ServiceManager()
