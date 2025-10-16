"""Unit tests for Gateway service."""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from main import app, manager


class TestGatewayHealth:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self):
        """Test health check when all services are healthy."""
        with patch('main.service_manager') as mock_manager:
            mock_manager.check_services_health.return_value = {
                "tts": True,
                "asr": True
            }
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "gateway"
            assert data["dependencies"]["tts"] is True
            assert data["dependencies"]["asr"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_degraded(self):
        """Test health check when some services are unhealthy."""
        with patch('main.service_manager') as mock_manager:
            mock_manager.check_services_health.return_value = {
                "tts": True,
                "asr": False
            }
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"


class TestGatewayWebSocket:
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
    
    @pytest.mark.asyncio
    async def test_websocket_empty_segments(self):
        """Test WebSocket with empty segments."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/tts") as websocket:
            message = {"segments": []}
            websocket.send_text(json.dumps(message))
            data = websocket.receive_text()
            response = json.loads(data)
            assert "error" in response


class TestEchoBytes:
    """Test echo-bytes endpoint."""
    
    def test_echo_bytes_invalid_sample_rate(self):
        """Test echo-bytes with invalid sample rate."""
        client = TestClient(app)
        
        # Test sample rate too low
        response = client.post(
            "/api/echo-bytes",
            params={"sr": 4000, "ch": 1},
            content=b"test audio"
        )
        assert response.status_code == 400
        
        # Test sample rate too high
        response = client.post(
            "/api/echo-bytes",
            params={"sr": 96000, "ch": 1},
            content=b"test audio"
        )
        assert response.status_code == 400
    
    def test_echo_bytes_invalid_channels(self):
        """Test echo-bytes with invalid channel count."""
        client = TestClient(app)
        
        # Test too few channels
        response = client.post(
            "/api/echo-bytes",
            params={"sr": 16000, "ch": 0},
            content=b"test audio"
        )
        assert response.status_code == 400
        
        # Test too many channels
        response = client.post(
            "/api/echo-bytes",
            params={"sr": 16000, "ch": 3},
            content=b"test audio"
        )
        assert response.status_code == 400
    
    def test_echo_bytes_empty_audio(self):
        """Test echo-bytes with empty audio data."""
        client = TestClient(app)
        response = client.post(
            "/api/echo-bytes",
            params={"sr": 16000, "ch": 1},
            content=b""
        )
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_echo_bytes_success(self):
        """Test successful echo-bytes request."""
        with patch('main.service_manager') as mock_manager:
            # Mock ASR response
            mock_asr_response = {
                "text": "Hello world",
                "segments": [{"start_ms": 0, "end_ms": 1000, "text": "Hello world"}]
            }
            mock_manager.asr_client.transcribe.return_value = mock_asr_response
            
            # Mock TTS streaming response
            async def mock_tts_stream():
                yield b"audio_chunk_1"
                yield b"audio_chunk_2"
            
            mock_manager.tts_client.synthesize_stream_http.return_value = mock_tts_stream()
            
            client = TestClient(app)
            response = client.post(
                "/api/echo-bytes",
                params={"sr": 16000, "ch": 1},
                content=b"test audio data"
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/octet-stream"
            # Note: Streaming response content might not be fully available in test client


class TestServiceClients:
    """Test service client functionality."""
    
    @pytest.mark.asyncio
    async def test_tts_service_client(self):
        """Test TTS service client."""
        from services import TTSServiceClient
        
        client = TTSServiceClient("http://test")
        
        # Test HTTP streaming (mocked)
        with patch('httpx.AsyncClient.stream') as mock_stream:
            mock_response = Mock()
            mock_response.aiter_bytes.return_value = [b"chunk1", b"chunk2"]
            mock_response.raise_for_status.return_value = None
            
            mock_stream.return_value.__aenter__.return_value = mock_response
            
            chunks = []
            async for chunk in client.synthesize_stream_http("test"):
                chunks.append(chunk)
            
            assert chunks == [b"chunk1", b"chunk2"]
    
    @pytest.mark.asyncio
    async def test_asr_service_client(self):
        """Test ASR service client."""
        from services import ASRServiceClient
        
        client = ASRServiceClient("http://test")
        
        # Test transcription (mocked)
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"text": "Hello world"}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = await client.transcribe(b"audio", 16000, 1, "en")
            
            assert result["text"] == "Hello world"


if __name__ == "__main__":
    pytest.main([__file__])
