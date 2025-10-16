"""Unit tests for ASR service."""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from main import app
from models import ASRResponseWithSegments


class TestASRHealth:
    """Test health check endpoint."""
    
    def test_health_check_healthy(self):
        """Test health check when service is healthy."""
        with patch('main.asr_engine') as mock_engine:
            mock_engine.is_healthy.return_value = True
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "asr-service"
    
    def test_health_check_unhealthy(self):
        """Test health check when service is unhealthy."""
        with patch('main.asr_engine') as mock_engine:
            mock_engine.is_healthy.return_value = False
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"


class TestASRSTT:
    """Test STT endpoint."""
    
    def test_stt_success(self):
        """Test successful STT request."""
        with patch('main.asr_engine') as mock_engine:
            # Mock transcription result
            mock_engine.transcribe.return_value = (
                "Hello world",
                [{"start_ms": 0, "end_ms": 1000, "text": "Hello world"}]
            )
            
            # Create test audio data (1 second of silence)
            sample_rate = 16000
            duration = 1.0
            audio_data = np.zeros(int(sample_rate * duration), dtype=np.int16)
            audio_bytes = audio_data.tobytes()
            
            client = TestClient(app)
            response = client.post(
                "/api/stt/bytes",
                params={"sr": sample_rate, "ch": 1, "lang": "en"},
                content=audio_bytes
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["text"] == "Hello world"
            assert len(data["segments"]) == 1
    
    def test_stt_invalid_sample_rate(self):
        """Test STT with invalid sample rate."""
        audio_bytes = b"test audio data"
        
        client = TestClient(app)
        
        # Test sample rate too low
        response = client.post(
            "/api/stt/bytes",
            params={"sr": 4000, "ch": 1},
            content=audio_bytes
        )
        assert response.status_code == 400
        
        # Test sample rate too high
        response = client.post(
            "/api/stt/bytes",
            params={"sr": 96000, "ch": 1},
            content=audio_bytes
        )
        assert response.status_code == 400
    
    def test_stt_invalid_channels(self):
        """Test STT with invalid channel count."""
        audio_bytes = b"test audio data"
        
        client = TestClient(app)
        
        # Test too few channels
        response = client.post(
            "/api/stt/bytes",
            params={"sr": 16000, "ch": 0},
            content=audio_bytes
        )
        assert response.status_code == 400
        
        # Test too many channels
        response = client.post(
            "/api/stt/bytes",
            params={"sr": 16000, "ch": 3},
            content=audio_bytes
        )
        assert response.status_code == 400
    
    def test_stt_empty_audio(self):
        """Test STT with empty audio data."""
        client = TestClient(app)
        response = client.post(
            "/api/stt/bytes",
            params={"sr": 16000, "ch": 1},
            content=b""
        )
        
        assert response.status_code == 400
    
    def test_stt_audio_too_long(self):
        """Test STT with audio exceeding maximum duration."""
        with patch('main.asr_engine') as mock_engine:
            mock_engine.transcribe.side_effect = ValueError("Audio duration exceeds maximum")
            
            # Create audio data longer than 15 seconds
            sample_rate = 16000
            duration = 16.0  # 16 seconds
            audio_data = np.zeros(int(sample_rate * duration), dtype=np.int16)
            audio_bytes = audio_data.tobytes()
            
            client = TestClient(app)
            response = client.post(
                "/api/stt/bytes",
                params={"sr": sample_rate, "ch": 1},
                content=audio_bytes
            )
            
            assert response.status_code == 400


class TestASREngine:
    """Test ASR engine functionality."""
    
    def test_audio_validation(self):
        """Test audio validation logic."""
        from asr_engine import ASREngine
        
        engine = ASREngine()
        
        # Test empty audio
        with pytest.raises(ValueError, match="Empty audio data"):
            engine._validate_audio(np.array([]), 16000)
        
        # Test audio too long
        long_audio = np.zeros(16000 * 16)  # 16 seconds
        with pytest.raises(ValueError, match="exceeds maximum"):
            engine._validate_audio(long_audio, 16000)
        
        # Test valid audio
        valid_audio = np.zeros(16000 * 5)  # 5 seconds
        # Should not raise exception
        engine._validate_audio(valid_audio, 16000)
    
    def test_audio_preprocessing(self):
        """Test audio preprocessing."""
        from asr_engine import ASREngine
        
        engine = ASREngine()
        
        # Test stereo to mono conversion
        stereo_audio = np.array([[1, 2], [3, 4], [5, 6]])
        mono_audio = engine._preprocess_audio(stereo_audio.tobytes(), 16000, 2)
        
        # Should be converted to mono
        assert len(mono_audio.shape) == 1
        assert len(mono_audio) == 3


if __name__ == "__main__":
    pytest.main([__file__])
