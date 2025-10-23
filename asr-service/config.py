
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="ASR_HOST")
    port: int = Field(default=8081, env="ASR_PORT")
    
    # Model configuration
    model_path: str = Field(default="/opt/models", env="ASR_MODEL_PATH")
    model_name: str = Field(default="base.en", env="ASR_MODEL_NAME")
    
    # Audio configuration
    sample_rate: int = Field(default=16000, env="ASR_SAMPLE_RATE")
    max_duration: int = Field(default=15, env="ASR_MAX_DURATION")
    
    # Logging configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    model_config = {
        "protected_namespaces": ("settings_",),
        "env_file": ".env",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()
