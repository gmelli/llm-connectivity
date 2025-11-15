"""
Pytest Fixtures for LLM Connectivity Tests

Provides reusable test fixtures for mocking provider responses and creating test clients.
"""

from unittest.mock import MagicMock, Mock

import pytest

# ==================== Mock Response Fixtures ====================


@pytest.fixture
def mock_openai_chat_response():
    """Mock OpenAI chat completion response."""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = "Test response from OpenAI"
    response.model = "gpt-4o"
    response.usage = Mock()
    response.usage.prompt_tokens = 10
    response.usage.completion_tokens = 20
    response.usage.total_tokens = 30
    return response


@pytest.fixture
def mock_openai_stream_chunk():
    """Mock OpenAI streaming chunk."""
    chunk = Mock()
    chunk.choices = [Mock()]
    chunk.choices[0].delta = Mock()
    chunk.choices[0].delta.content = "chunk"
    chunk.choices[0].finish_reason = None
    return chunk


@pytest.fixture
def mock_openai_embedding_response():
    """Mock OpenAI embeddings response."""
    response = Mock()
    response.data = [Mock(), Mock()]
    response.data[0].embedding = [0.1, 0.2, 0.3]  # 3-dim for testing
    response.data[1].embedding = [0.4, 0.5, 0.6]
    response.model = "text-embedding-3-small"
    response.usage = Mock()
    response.usage.prompt_tokens = 5
    response.usage.total_tokens = 5
    return response


@pytest.fixture
def mock_anthropic_chat_response():
    """Mock Anthropic chat completion response."""
    response = Mock()
    response.content = [Mock()]
    response.content[0].text = "Test response from Anthropic"
    response.model = "claude-3-opus-20240229"
    response.usage = Mock()
    response.usage.input_tokens = 10
    response.usage.output_tokens = 20
    return response


@pytest.fixture
def mock_google_chat_response():
    """Mock Google chat completion response."""
    response = Mock()
    response.text = "Test response from Google"
    response.candidates = [Mock()]
    response.candidates[0].finish_reason = "STOP"
    return response


# ==================== Test Data Fixtures ====================


@pytest.fixture
def sample_messages():
    """Sample chat messages for testing."""
    return [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hello"},
    ]


@pytest.fixture
def sample_texts():
    """Sample texts for embedding testing."""
    return ["Hello world", "Test embedding"]


# ==================== Client Fixtures ====================


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.embeddings = MagicMock()
    client.timeout = 60.0
    return client


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    client = MagicMock()
    client.messages = MagicMock()
    client.timeout = 60.0
    return client
