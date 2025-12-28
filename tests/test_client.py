# tests/test_client.py
"""
Tests for the Tensalis Python SDK client.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from tensalis import TensalisClient, VerificationResult
from tensalis.exceptions import (
    TensalisError,
    TensalisAPIError,
    TensalisAuthenticationError,
    TensalisTimeoutError,
)


class TestTensalisClient:
    """Tests for TensalisClient initialization and configuration."""
    
    def test_client_init_with_api_key(self):
        """Client should initialize with valid API key."""
        client = TensalisClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.endpoint == "https://api.tensalis.com/v1"
        assert client.mode == "balanced"
    
    def test_client_init_without_api_key_raises_error(self):
        """Client should raise error without API key."""
        with pytest.raises(TensalisError, match="API key is required"):
            TensalisClient(api_key="")
    
    def test_client_init_with_custom_endpoint(self):
        """Client should accept custom endpoint."""
        client = TensalisClient(
            api_key="test-key",
            endpoint="https://custom.tensalis.com/v1"
        )
        assert client.endpoint == "https://custom.tensalis.com/v1"
    
    def test_client_init_strips_trailing_slash(self):
        """Client should strip trailing slash from endpoint."""
        client = TensalisClient(
            api_key="test-key",
            endpoint="https://api.tensalis.com/v1/"
        )
        assert client.endpoint == "https://api.tensalis.com/v1"
    
    def test_client_init_with_mode(self):
        """Client should accept verification mode."""
        client = TensalisClient(api_key="test-key", mode="strict")
        assert client.mode == "strict"
    
    def test_client_context_manager(self):
        """Client should work as context manager."""
        with TensalisClient(api_key="test-key") as client:
            assert client.api_key == "test-key"


class TestVerificationResult:
    """Tests for VerificationResult class."""
    
    def test_verified_result(self):
        """Verified result should have correct properties."""
        result = VerificationResult({
            "status": "VERIFIED",
            "latency_ms": 5
        })
        assert result.status == "VERIFIED"
        assert result.is_verified is True
        assert result.is_blocked is False
        assert result.severity is None
    
    def test_blocked_result(self):
        """Blocked result should have correct properties."""
        result = VerificationResult({
            "status": "BLOCKED",
            "severity": "HIGH",
            "reason": "Contradiction detected",
            "confidence": 0.94,
            "layer": "cascading_nli",
            "latency_ms": 12
        })
        assert result.status == "BLOCKED"
        assert result.is_blocked is True
        assert result.is_verified is False
        assert result.severity == "HIGH"
        assert result.reason == "Contradiction detected"
        assert result.confidence == 0.94
        assert result.layer == "cascading_nli"
    
    def test_result_to_dict(self):
        """Result should convert to dictionary."""
        data = {"status": "VERIFIED", "latency_ms": 5}
        result = VerificationResult(data)
        assert result.to_dict() == data
    
    def test_result_repr(self):
        """Result should have readable repr."""
        result = VerificationResult({"status": "BLOCKED", "severity": "HIGH"})
        assert "BLOCKED" in repr(result)
        assert "HIGH" in repr(result)


class TestVerify:
    """Tests for the verify method."""
    
    @patch.object(TensalisClient, '_request')
    def test_verify_success(self, mock_request):
        """Verify should return VerificationResult on success."""
        mock_request.return_value = {
            "status": "VERIFIED",
            "latency_ms": 5
        }
        
        client = TensalisClient(api_key="test-key")
        result = client.verify(
            response="The sky is blue.",
            context=["The sky appears blue during clear days."]
        )
        
        assert isinstance(result, VerificationResult)
        assert result.is_verified
        mock_request.assert_called_once()
    
    @patch.object(TensalisClient, '_request')
    def test_verify_blocked(self, mock_request):
        """Verify should return blocked result for hallucinations."""
        mock_request.return_value = {
            "status": "BLOCKED",
            "severity": "HIGH",
            "reason": "Factual contradiction",
            "layer": "cascading_nli"
        }
        
        client = TensalisClient(api_key="test-key")
        result = client.verify(
            response="Returns allowed within 90 days.",
            context=["Returns accepted within 30 days."]
        )
        
        assert result.is_blocked
        assert result.severity == "HIGH"
    
    @patch.object(TensalisClient, '_request')
    def test_verify_with_string_context(self, mock_request):
        """Verify should accept string context."""
        mock_request.return_value = {"status": "VERIFIED"}
        
        client = TensalisClient(api_key="test-key")
        client.verify(
            response="Test response.",
            context="Single context string."
        )
        
        call_args = mock_request.call_args
        payload = call_args[0][2]
        assert isinstance(payload["reference_facts"], list)
    
    @patch.object(TensalisClient, '_request')
    def test_verify_with_metadata(self, mock_request):
        """Verify should pass metadata to API."""
        mock_request.return_value = {"status": "VERIFIED"}
        
        client = TensalisClient(api_key="test-key")
        client.verify(
            response="Test response.",
            context=["Test context."],
            metadata={"user_id": "123", "session": "abc"}
        )
        
        call_args = mock_request.call_args
        payload = call_args[0][2]
        assert payload["metadata"] == {"user_id": "123", "session": "abc"}


class TestVerifyBatch:
    """Tests for batch verification."""
    
    @patch.object(TensalisClient, '_request')
    def test_verify_batch_success(self, mock_request):
        """Batch verify should return list of results."""
        mock_request.return_value = {
            "results": [
                {"status": "VERIFIED"},
                {"status": "BLOCKED", "severity": "HIGH"}
            ]
        }
        
        client = TensalisClient(api_key="test-key")
        results = client.verify_batch([
            {"response": "Answer 1", "context": ["Fact 1"]},
            {"response": "Answer 2", "context": ["Fact 2"]},
        ])
        
        assert len(results) == 2
        assert results[0].is_verified
        assert results[1].is_blocked


class TestErrorHandling:
    """Tests for error handling."""
    
    @patch('tensalis.client.requests.Session.request')
    def test_api_error_handling(self, mock_request):
        """Client should raise TensalisAPIError for API errors."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.content = b'{"error": "Invalid request"}'
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_request.return_value = mock_response
        
        client = TensalisClient(api_key="test-key")
        
        with pytest.raises(TensalisAPIError) as exc_info:
            client.verify(response="test", context=["test"])
        
        assert exc_info.value.status_code == 400
    
    @patch('tensalis.client.requests.Session.request')
    def test_timeout_handling(self, mock_request):
        """Client should raise TensalisTimeoutError on timeout."""
        mock_request.side_effect = requests.Timeout("Connection timed out")
        
        client = TensalisClient(api_key="test-key", retries=1)
        
        with pytest.raises(TensalisTimeoutError):
            client.verify(response="test", context=["test"])


class TestHealthAndUsage:
    """Tests for health and usage endpoints."""
    
    @patch.object(TensalisClient, '_request')
    def test_health_check(self, mock_request):
        """Health check should return status."""
        mock_request.return_value = {"status": "healthy", "latency_ms": 2}
        
        client = TensalisClient(api_key="test-key")
        result = client.health()
        
        assert result["status"] == "healthy"
        mock_request.assert_called_with("GET", "/health")
    
    @patch.object(TensalisClient, '_request')
    def test_usage_check(self, mock_request):
        """Usage check should return metrics."""
        mock_request.return_value = {
            "requests_today": 1000,
            "limit": 10000
        }
        
        client = TensalisClient(api_key="test-key")
        result = client.usage()
        
        assert result["requests_today"] == 1000
        mock_request.assert_called_with("GET", "/usage")
