"""Unit tests for ASR service."""

import pytest
import numpy as np
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from main import app


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
    
    def test_stt_endpoint_route(self):
        """Test that STT endpoint route exists."""
        # Just test that the route is defined
        from main import app
        routes = [route.path for route in app.routes]
        assert "/api/stt/bytes" in routes


class TestASREngine:
    """Test ASR engine functionality."""
    
    def test_engine_initialization(self):
        """Test ASR engine initialization."""
        from asr_engine import ASREngine
        
        # This should not raise an exception
        engine = ASREngine()
        assert engine is not None