
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any

from config import settings
from logger import get_logger
from models import (
    ASRResponse, 
    ASRResponseWithSegments, 
    HealthResponse,
    ErrorResponse
)
from asr_engine import asr_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ASR service", 
               host=settings.host, 
               port=settings.port,
               model_name=settings.model_name,
               sample_rate=settings.sample_rate)
    yield
    logger.info("Shutting down ASR service")


app = FastAPI(
    title="ASR Service",
    description="Automatic Speech Recognition service using Whisper",
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
    try:
        is_healthy = asr_engine.is_healthy()
        status = "healthy" if is_healthy else "unhealthy"
        
        logger.info("Health check", status=status)
        
        return HealthResponse(
            status=status,
            service="asr-service"
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Service unhealthy")


@app.post("/api/stt/bytes", response_model=ASRResponseWithSegments)
async def stt_bytes(
    request: Request,
    sr: int,
    ch: int,
    lang: str = "en",
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
        
        logger.info("STT request received", 
                   audio_size=len(audio_bytes),
                   sample_rate=sr,
                   channels=ch,
                   language=lang,
                   format=fmt)
        
        text, segments = asr_engine.transcribe(
            audio_bytes=audio_bytes,
            sample_rate=sr,
            channels=ch,
            language=lang
        )
        
        if segments:
            response = ASRResponseWithSegments(
                text=text,
                segments=segments
            )
        else:
            response = ASRResponseWithSegments(
                text=text,
                segments=None
            )
        
        logger.info("STT request completed", 
                   text_length=len(text),
                   segments_count=len(segments) if segments else 0)
        
        return response
        
    except ValueError as e:
        logger.error("STT validation error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("STT request failed", error=str(e))
        raise HTTPException(status_code=500, detail="Speech recognition failed")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error("HTTP exception", 
                status_code=exc.status_code,
                detail=exc.detail,
                path=request.url.path)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "detail": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", 
                error=str(exc),
                path=request.url.path)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred"
        }
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
