"""Pytest configuration and fixtures for llm-connectivity tests."""

import pytest


@pytest.fixture
def mock_api_key() -> str:
    """Return a mock API key for testing."""
    return "sk-test-mock-api-key-1234567890"


# Additional fixtures will be added as needed during test implementation
