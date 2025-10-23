
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="TTS_HOST")
    port: int = Field(default=8082, env="TTS_PORT")
    
    # Model configuration
    model_path: str = Field(default="/opt/models", env="TTS_MODEL_PATH")
    model_name: str = Field(default="espeak", env="TTS_MODEL_NAME")
    
    # Audio configuration
    sample_rate: int = Field(default=22050, env="TTS_SAMPLE_RATE")
    chunk_size: int = Field(default=1024, env="TTS_CHUNK_SIZE")
    
    # Logging configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()
