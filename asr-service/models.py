
from typing import Optional, List
from pydantic import BaseModel, Field


class ASRRequest(BaseModel):
    sr: int = Field(..., description="Sample rate", ge=8000, le=48000)
    ch: int = Field(..., description="Number of channels", ge=1, le=2)
    lang: str = Field(default="en", description="Language code")
    fmt: Optional[str] = Field(default="s16le", description="Audio format")


class ASRResponse(BaseModel):
    text: str = Field(..., description="Recognized text")


class ASRSegment(BaseModel):
    start_ms: int = Field(..., description="Start time in milliseconds")
    end_ms: int = Field(..., description="End time in milliseconds")
    text: str = Field(..., description="Segment text")


class ASRResponseWithSegments(BaseModel):
    text: str = Field(..., description="Full recognized text")
    segments: Optional[List[ASRSegment]] = Field(None, description="Text segments with timing")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
