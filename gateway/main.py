
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any

from config import settings
from logger import get_logger
from models import (
    TTSRequest, 
    SegmentRequest, 
    HealthResponse,
    ErrorResponse,
    WebSocketMessage,
    WebSocketEndMessage
)
from services import service_manager

logger = get_logger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[websocket] = client_id
        logger.info("WebSocket connection established", client_id=client_id)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            client_id = self.active_connections.pop(websocket)
            logger.info("WebSocket connection closed", client_id=client_id)
    
    async def send_binary(self, websocket: WebSocket, data: bytes):
        await websocket.send_bytes(data)
    
    async def send_text(self, websocket: WebSocket, message: str):
        await websocket.send_text(message)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Gateway service", 
               host=settings.host, 
               port=settings.port,
               tts_service_url=settings.tts_service_url,
               asr_service_url=settings.asr_service_url)
    yield
    await service_manager.close()
    logger.info("Shutting down Gateway service")


app = FastAPI(
    title="Gateway Service",
    description="Gateway service for TTS and ASR integration",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        # Check service dependencies
        dependencies = await service_manager.check_services_health()
        
        all_healthy = all(dependencies.values())
        status = "healthy" if all_healthy else "degraded"
        
        logger.info("Health check", status=status, dependencies=dependencies)
        
        return HealthResponse(
            status=status,
            service="gateway",
            dependencies=dependencies
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Service unhealthy")


@app.websocket("/ws/tts")
async def tts_websocket(websocket: WebSocket):
    client_id = f"client_{id(websocket)}"
    
    try:
        await manager.connect(websocket, client_id)
        
        while True:
            # Receive text message
            data = await websocket.receive_text()
            
            try:
                # Parse message
                message_data = json.loads(data)
                
                # Handle different message types
                if "text" in message_data:
                    # Single text message
                    text = message_data["text"]
                    
                    if not text or not text.strip():
                        await websocket.send_text(json.dumps({
                            "error": "Empty text provided"
                        }))
                        continue
                    
                    logger.info("WebSocket TTS request", 
                               client_id=client_id, 
                               text_length=len(text))
                    
                    # Stream audio using WebSocket
                    await service_manager.tts_client.synthesize_stream_websocket(websocket, text)
                    
                elif "segments" in message_data:
                    # Multiple segments
                    segments = message_data["segments"]
                    
                    if not segments:
                        await websocket.send_text(json.dumps({
                            "error": "Empty segments provided"
                        }))
                        continue
                    
                    logger.info("WebSocket TTS segments request", 
                               client_id=client_id, 
                               segments_count=len(segments))
                    
                    # Process each segment
                    for segment in segments:
                        if "text" in segment:
                            text = segment["text"]
                            if text and text.strip():
                                await service_manager.tts_client.synthesize_stream_websocket(websocket, text)
                
                logger.info("WebSocket TTS request completed", client_id=client_id)
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "error": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error("WebSocket TTS error", 
                           client_id=client_id, 
                           error=str(e))
                await websocket.send_text(json.dumps({
                    "error": f"TTS generation failed: {str(e)}"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket disconnected", client_id=client_id)
    except Exception as e:
        logger.error("WebSocket connection error", 
                    client_id=client_id, 
                    error=str(e))
        manager.disconnect(websocket)


@app.post("/api/echo-bytes", response_class=StreamingResponse)
async def echo_bytes(
    request: Request,
    sr: int = 16000,
    ch: int = 1,
    fmt: str = "s16le"
):
    try:
        if sr < 8000 or sr > 48000:
            raise HTTPException(
                status_code=400, 
                detail="Sample rate must be between 8000 and 48000 Hz"
            )
        
        if ch < 1 or ch > 2:
            raise HTTPException(
                status_code=400, 
                detail="Number of channels must be 1 or 2"
            )
        
        audio_bytes = await request.body()
        
        if not audio_bytes:
            raise HTTPException(
                status_code=400, 
                detail="No audio data provided"
            )
        
        logger.info("Echo bytes request received", 
                   audio_size=len(audio_bytes),
                   sample_rate=sr,
                   channels=ch)
        
        try:
            logger.info("Calling ASR service", 
                       audio_size=len(audio_bytes),
                       sample_rate=sr,
                       channels=ch)
            
            asr_result = await service_manager.asr_client.transcribe(
                audio_bytes=audio_bytes,
                sample_rate=sr,
                channels=ch,
                language="en"
            )
            
            logger.info("ASR result received", result=asr_result)
            
            recognized_text = asr_result.get("text", "")
            segments = asr_result.get("segments", [])
            
            logger.info("ASR completed", 
                       text_length=len(recognized_text),
                       segments_count=len(segments))
            
            # Log the recognized text for debugging
            print(f"\n{'='*50}")
            print("РАСПОЗНАННЫЙ ТЕКСТ:")
            print(f"📝 {recognized_text}")
            if segments:
                print(f"📊 Сегменты ({len(segments)}):")
                for i, segment in enumerate(segments, 1):
                    print(f"  {i}. {segment}")
            print("="*50)
            
            if not recognized_text.strip():
                logger.warning("No text recognized from audio")
                return StreamingResponse(
                    iter([]),
                    media_type="application/octet-stream",
                    headers={
                        "Content-Type": "application/octet-stream",
                        "X-Sample-Rate": str(sr),
                        "X-Channels": str(ch),
                        "X-Recognized-Text": "",
                        "X-Segments": "[]"
                    }
                )
            
            import json
            segments_json = json.dumps(segments) if segments else "[]"
            
            async def generate_echo_stream():
                try:
                    # Synthesize recognized text using TTS
                    async for audio_chunk in service_manager.tts_client.synthesize_stream_http(recognized_text):
                        yield audio_chunk
                    
                    logger.info("Echo bytes request completed")
                    
                except Exception as e:
                    logger.error("Echo bytes generation failed", error=str(e))
                    return
            
            return StreamingResponse(
                generate_echo_stream(),
                media_type="application/octet-stream",
                headers={
                    "Content-Type": "application/octet-stream",
                    "X-Sample-Rate": str(sr),
                    "X-Channels": str(ch),
                    "X-Recognized-Text": recognized_text,
                    "X-Segments": segments_json
                }
            )
            
        except Exception as e:
            logger.error("ASR request failed", error=str(e))
            return StreamingResponse(
                iter([]),
                media_type="application/octet-stream",
                headers={
                    "Content-Type": "application/octet-stream",
                    "X-Sample-Rate": str(sr),
                    "X-Channels": str(ch),
                    "X-Recognized-Text": "",
                    "X-Segments": "[]"
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Echo bytes request failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    logger.error("HTTP exception", 
                status_code=exc.status_code,
                detail=exc.detail,
                path=request.url.path)
    
    return ErrorResponse(
        error=f"HTTP {exc.status_code}",
        detail=exc.detail
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler."""
    logger.error("Unhandled exception", 
                error=str(exc),
                path=request.url.path)
    
    return ErrorResponse(
        error="Internal server error",
        detail="An unexpected error occurred"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False
    )
