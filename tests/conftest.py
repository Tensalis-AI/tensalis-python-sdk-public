# tests/conftest.py
"""
Pytest configuration and fixtures for Tensalis SDK tests.
"""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_api_response():
    """Factory fixture for creating mock API responses."""
    def _create_response(status_code=200, data=None):
        response = Mock()
        response.status_code = status_code
        response.content = b'{}'
        response.json.return_value = data or {}
        return response
    return _create_response


@pytest.fixture
def verified_response(mock_api_response):
    """Mock verified response."""
    return mock_api_response(200, {
        "status": "VERIFIED",
        "latency_ms": 5
    })


@pytest.fixture
def blocked_response(mock_api_response):
    """Mock blocked response."""
    return mock_api_response(200, {
        "status": "BLOCKED",
        "severity": "HIGH",
        "reason": "Contradiction detected",
        "confidence": 0.94,
        "layer": "cascading_nli",
        "latency_ms": 12
    })


@pytest.fixture
def sample_context():
    """Sample context documents for testing."""
    return [
        "Returns are accepted within 30 days of purchase.",
        "Refunds are processed within 5-7 business days.",
        "Items must be in original packaging."
    ]
