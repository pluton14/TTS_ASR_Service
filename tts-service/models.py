"""Pydantic models for TTS service."""

from typing import Optional, List
from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """TTS request model."""
    text: str = Field(..., description="Text to synthesize", min_length=1, max_length=1000)


class TTSResponse(BaseModel):
    """TTS response model."""
    message: str = Field(..., description="Response message")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    text: str = Field(..., description="Text to synthesize")


class WebSocketEndMessage(BaseModel):
    """WebSocket end message model."""
    type: str = Field(default="end", description="Message type")


class SegmentRequest(BaseModel):
    """Segment-based TTS request model."""
    segments: List[dict] = Field(..., description="List of text segments to synthesize")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
