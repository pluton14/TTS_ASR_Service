"""Unit tests for TTS service."""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from main import app, manager
from models import TTSRequest


class TestTTSHealth:
    """Test health check endpoint."""
    
    def test_health_check_healthy(self):
        """Test health check when service is healthy."""
        with patch('main.tts_engine') as mock_engine:
            mock_engine.is_healthy.return_value = True
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "tts-service"
    
    def test_health_check_unhealthy(self):
        """Test health check when service is unhealthy."""
        with patch('main.tts_engine') as mock_engine:
            mock_engine.is_healthy.return_value = False
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"


class TestTTSHTTP:
    """Test HTTP TTS endpoint."""
    
    @pytest.mark.asyncio
    async def test_tts_http_success(self):
        """Test successful HTTP TTS request."""
        with patch('main.tts_engine') as mock_engine:
            # Mock the streaming response
            async def mock_stream(text):
                yield b"audio_chunk_1"
                yield b"audio_chunk_2"
            
            mock_engine.synthesize_stream.return_value = mock_stream("test")
            
            client = TestClient(app)
            response = client.post("/api/tts", json={"text": "Hello world"})
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/octet-stream"
            assert b"audio_chunk_1" in response.content
            assert b"audio_chunk_2" in response.content
    
    def test_tts_http_empty_text(self):
        """Test HTTP TTS with empty text."""
        client = TestClient(app)
        response = client.post("/api/tts", json={"text": ""})
        
        assert response.status_code == 422  # Validation error
    
    def test_tts_http_missing_text(self):
        """Test HTTP TTS with missing text field."""
        client = TestClient(app)
        response = client.post("/api/tts", json={})
        
        assert response.status_code == 422  # Validation error


class TestTTSWebSocket:
    """Test WebSocket TTS endpoint."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/tts") as websocket:
            assert websocket in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_websocket_invalid_json(self):
        """Test WebSocket with invalid JSON."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/tts") as websocket:
            websocket.send_text("invalid json")
            data = websocket.receive_text()
            response = json.loads(data)
            assert "error" in response
    
    @pytest.mark.asyncio
    async def test_websocket_empty_text(self):
        """Test WebSocket with empty text."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/tts") as websocket:
            message = {"text": ""}
            websocket.send_text(json.dumps(message))
            data = websocket.receive_text()
            response = json.loads(data)
            assert "error" in response


class TestTTSValidation:
    """Test input validation."""
    
    def test_text_length_validation(self):
        """Test text length validation."""
        client = TestClient(app)
        
        # Test text too long
        long_text = "a" * 1001
        response = client.post("/api/tts", json={"text": long_text})
        assert response.status_code == 422
        
        # Test valid text length
        valid_text = "a" * 500
        with patch('main.tts_engine') as mock_engine:
            mock_engine.synthesize_stream.return_value = AsyncMock()
            response = client.post("/api/tts", json={"text": valid_text})
            # Should not be a validation error (might be other errors, but not 422)
            assert response.status_code != 422


if __name__ == "__main__":
    pytest.main([__file__])
