"""Unit tests for TTS service."""

import pytest
from unittest.mock import patch, MagicMock, Mock
from fastapi.testclient import TestClient
from main import app


class TestTTSHealth:
    
    def test_health_check_healthy(self):
        with patch('main.tts_engine') as mock_engine:
            mock_engine.is_healthy.return_value = True
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "tts-service"
    
    def test_health_check_unhealthy(self):
        with patch('main.tts_engine') as mock_engine:
            mock_engine.is_healthy.return_value = False
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"


class TestTTSHTTP:
    
    def test_tts_http_empty_text(self):
        client = TestClient(app)
        response = client.post("/api/tts", json={"text": ""})
        
        assert response.status_code == 422
    
    def test_tts_http_missing_text(self):
        client = TestClient(app)
        response = client.post("/api/tts", json={})
        
        assert response.status_code == 422


class TestTTSValidation:
    
    @patch('main.tts_engine.synthesize_stream')
    @patch('pydub.AudioSegment.from_mp3')
    @patch('gtts.gTTS')
    def test_valid_text(self, mock_gtts, mock_from_mp3, mock_synthesize):
        mock_gtts_instance = MagicMock()
        mock_gtts.return_value = mock_gtts_instance
        mock_gtts_instance.save.return_value = None
        
        mock_audio = MagicMock()
        mock_audio.export.return_value = b"fake_audio_data"
        mock_from_mp3.return_value = mock_audio
        
        mock_synthesize.return_value = [b"chunk1", b"chunk2"]
        
        client = TestClient(app)
        response = client.post("/api/tts", json={"text": "Hello world"})
        
        assert response.status_code == 200