"""
API Integration Tests

Tests the /query endpoint and overall system functionality
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["status"] == "running"


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_query_endpoint_basic():
    """Test basic query endpoint."""
    payload = {
        "prompt": "What is the price of NVDA?"
    }
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "answer" in data
    assert "confidence" in data
    assert "data_timestamp" in data
    assert isinstance(data["confidence"], float)
    assert 0.0 <= data["confidence"] <= 1.0


def test_query_endpoint_with_nvda():
    """Test query with NVDA ticker."""
    payload = {
        "prompt": "How much is NVDA stock trading at?"
    }
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "answer" in data
    # Check that answer contains the ticker
    assert "NVDA" in data["answer"] or "nvda" in data["answer"].lower()


def test_query_endpoint_missing_prompt():
    """Test query endpoint with missing prompt."""
    response = client.post("/query", json={})
    assert response.status_code == 422  # Validation error


def test_query_endpoint_response_structure():
    """Test that response has all required fields."""
    payload = {
        "prompt": "Tell me about NVDA"
    }
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    required_fields = ["answer", "citations", "confidence", "data_timestamp"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Check types
    assert isinstance(data["answer"], str)
    assert isinstance(data["citations"], list)
    assert isinstance(data["confidence"], float)
    assert isinstance(data["data_timestamp"], str)


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])

