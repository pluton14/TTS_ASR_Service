"""Pydantic models for Gateway service."""

from typing import Optional, List, Union
from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """TTS request model."""
    text: str = Field(..., description="Text to synthesize", min_length=1, max_length=1000)


class SegmentRequest(BaseModel):
    """Segment-based TTS request model."""
    text: str = Field(..., description="Text to synthesize")
    segments: Optional[List[dict]] = Field(None, description="List of text segments to synthesize")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    dependencies: Optional[dict] = Field(None, description="Dependency status")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    text: str = Field(..., description="Text to synthesize")


class WebSocketEndMessage(BaseModel):
    """WebSocket end message model."""
    type: str = Field(default="end", description="Message type")
