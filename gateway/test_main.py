"""Unit tests for Gateway service."""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from main import app


class TestGatewayHealth:
    """Test health check endpoint."""
    
    def test_health_check_endpoint_exists(self):
        """Test that health check endpoint exists."""
        client = TestClient(app)
        
        # Test that endpoint exists
        response = client.get("/health")
        
        # Should get some response (not 404)
        assert response.status_code != 404


class TestEchoBytes:
    """Test echo-bytes endpoint."""
    
    def test_echo_bytes_endpoint_exists(self):
        """Test that echo-bytes endpoint exists and responds."""
        client = TestClient(app)
        
        # Test that endpoint exists (even if it fails validation)
        response = client.post(
            "/api/echo-bytes",
            params={"sr": 16000, "ch": 1},
            content=b"test audio"
        )
        
        # Should get some response (not 404)
        assert response.status_code != 404


class TestServiceClients:
    """Test service client functionality."""
    
    def test_service_manager_initialization(self):
        """Test service manager initialization."""
        from services import ServiceManager
        
        # This should not raise an exception
        manager = ServiceManager()
        assert manager is not None