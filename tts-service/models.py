
from typing import Optional, List
from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize", min_length=1, max_length=1000)


class TTSResponse(BaseModel):
    message: str = Field(..., description="Response message")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")


class WebSocketMessage(BaseModel):
    text: str = Field(..., description="Text to synthesize")


class WebSocketEndMessage(BaseModel):
    type: str = Field(default="end", description="Message type")


class SegmentRequest(BaseModel):
    """Segment-based TTS request model."""
    segments: List[dict] = Field(..., description="List of text segments to synthesize")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
