"""Main FastAPI application for TTS service."""

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any

from config import settings
from logger import get_logger
from models import (
    TTSRequest, 
    TTSResponse, 
    HealthResponse, 
    WebSocketMessage, 
    WebSocketEndMessage,
    ErrorResponse
)
from tts_engine import tts_engine

logger = get_logger(__name__)

# WebSocket connection manager
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
    """Application lifespan manager."""
    logger.info("Starting TTS service", 
               host=settings.host, 
               port=settings.port,
               sample_rate=settings.sample_rate)
    yield
    logger.info("Shutting down TTS service")


app = FastAPI(
    title="TTS Service",
    description="Text-to-Speech service with streaming support",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        is_healthy = tts_engine.is_healthy()
        status = "healthy" if is_healthy else "unhealthy"
        
        logger.info("Health check", status=status)
        
        return HealthResponse(
            status=status,
            service="tts-service"
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Service unhealthy")


@app.post("/api/tts", response_class=StreamingResponse)
async def tts_http(request: TTSRequest):
    """HTTP endpoint for TTS with streaming response."""
    try:
        logger.info("HTTP TTS request", text_length=len(request.text))
        
        async def generate_audio():
            """Generate audio stream."""
            try:
                async for chunk in tts_engine.synthesize_stream(request.text):
                    yield chunk
            except Exception as e:
                logger.error("HTTP TTS streaming failed", error=str(e))
                # Cannot raise HTTPException here as response has already started
                # Just log the error and stop streaming
                return
        
        return StreamingResponse(
            generate_audio(),
            media_type="application/octet-stream",
            headers={
                "Content-Type": "application/octet-stream",
                "X-Sample-Rate": str(settings.sample_rate),
                "X-Channels": "1"
            }
        )
        
    except Exception as e:
        logger.error("HTTP TTS request failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/tts")
async def tts_websocket(websocket: WebSocket):
    """WebSocket endpoint for TTS streaming."""
    client_id = f"client_{id(websocket)}"
    
    try:
        await manager.connect(websocket, client_id)
        
        while True:
            # Receive text message
            data = await websocket.receive_text()
            
            try:
                # Parse message
                import json
                message_data = json.loads(data)
                
                if "text" not in message_data:
                    await websocket.send_text(json.dumps({
                        "error": "Missing 'text' field in request"
                    }))
                    continue
                
                text = message_data["text"]
                
                if not text or not text.strip():
                    await websocket.send_text(json.dumps({
                        "error": "Empty text provided"
                    }))
                    continue
                
                logger.info("WebSocket TTS request", 
                           client_id=client_id, 
                           text_length=len(text))
                
                # Stream audio chunks
                async for chunk in tts_engine.synthesize_stream(text):
                    await manager.send_binary(websocket, chunk)
                
                # Send end message
                end_message = WebSocketEndMessage()
                await manager.send_text(websocket, end_message.model_dump_json())
                
                logger.info("WebSocket TTS completed", client_id=client_id)
                
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False
    )
