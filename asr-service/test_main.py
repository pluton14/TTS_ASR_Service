"""Unit tests for ASR service."""

import pytest
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
from main import app


class TestASRHealth:
    
    def test_health_check_healthy(self):
        with patch('main.asr_engine') as mock_engine:
            mock_engine.is_healthy.return_value = True
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "asr-service"
    
    def test_health_check_unhealthy(self):
        with patch('main.asr_engine') as mock_engine:
            mock_engine.is_healthy.return_value = False
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"


class TestASRSTT:
    
    def test_stt_endpoint_route(self):
        from main import app
        routes = [route.path for route in app.routes]
        assert "/api/stt/bytes" in routes


class TestASREngine:
    
    @patch('whisper.load_model')
    def test_engine_initialization(self, mock_load_model):
        from asr_engine import ASREngine
        
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        engine = ASREngine()
        
        assert engine.model == mock_model
        mock_load_model.assert_called_once_with("base.en", download_root="/opt/models")