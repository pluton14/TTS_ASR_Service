
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="GATEWAY_HOST")
    port: int = Field(default=8000, env="GATEWAY_PORT")
    
    # Service URLs
    tts_service_url: str = Field(default="http://tts-service:8082", env="TTS_SERVICE_URL")
    asr_service_url: str = Field(default="http://asr-service:8081", env="ASR_SERVICE_URL")
    
    # Logging configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "protected_namespaces": ("settings_",)
    }


# Global settings instance
settings = Settings()
