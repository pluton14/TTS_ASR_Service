"""Unit tests for TTS service."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app


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


class TestTTSValidation:
    """Test input validation."""
    
    def test_valid_text(self):
        """Test valid text input."""
        client = TestClient(app)
        
        # Test normal text
        response = client.post("/api/tts", json={"text": "Hello world"})
        
        # Should work
        assert response.status_code == 200