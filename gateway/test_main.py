"""Unit tests for Gateway service."""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from main import app


class TestGatewayHealth:
    
    def test_health_check_endpoint_exists(self):
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code != 404


class TestEchoBytes:
    
    def test_echo_bytes_endpoint_exists(self):
        client = TestClient(app)
        
        response = client.post(
            "/api/echo-bytes",
            params={"sr": 16000, "ch": 1},
            content=b"test audio"
        )
        
        assert response.status_code != 404


class TestServiceClients:
    
    def test_service_manager_initialization(self):
        from main import service_manager
        
        assert service_manager.tts_client is not None
        assert service_manager.asr_client is not None