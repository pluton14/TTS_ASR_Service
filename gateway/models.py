
from typing import Optional, List, Union
from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize", min_length=1, max_length=1000)


class SegmentRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    segments: Optional[List[dict]] = Field(None, description="List of text segments to synthesize")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    dependencies: Optional[dict] = Field(None, description="Dependency status")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")


class WebSocketMessage(BaseModel):
    text: str = Field(..., description="Text to synthesize")


class WebSocketEndMessage(BaseModel):
    type: str = Field(default="end", description="Message type")
