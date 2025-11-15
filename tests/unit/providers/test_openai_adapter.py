"""
Unit Tests for OpenAI Adapter

Tests OpenAI adapter functionality with mocked API responses.
Target: 95%+ coverage on openai_adapter.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from llm_connectivity.providers.openai_adapter import (
    OpenAIAdapter,
    ChatResponse,
    StreamChunk,
    EmbeddingResponse,
)
from llm_connectivity.errors import (
    RateLimitError,
    AuthenticationError,
    NetworkError,
    ModelNotFoundError,
    ContextWindowExceededError,
    ValidationError,
)


class TestOpenAIAdapterInitialization:
    """Test OpenAIAdapter initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        adapter = OpenAIAdapter(api_key="sk-test123")
        assert adapter.client is not None
        assert adapter.client.timeout == 60.0

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        adapter = OpenAIAdapter(api_key="sk-test123", timeout=120.0)
        assert adapter.client.timeout == 120.0

    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-env-key"})
    def test_init_from_env_var(self):
        """Test initialization from environment variable."""
        adapter = OpenAIAdapter()
        assert adapter.client is not None


class TestOpenAIAdapterChat:
    """Test OpenAI chat completion."""

    @patch("llm_connectivity.providers.openai_adapter.OpenAI")
    def test_chat_success(self, mock_openai_class, mock_openai_chat_response):
        """Test successful chat completion."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_chat_response

        # Create adapter and call chat
        adapter = OpenAIAdapter(api_key="sk-test123")
        adapter.client = mock_client  # Replace with our mock

        messages = [{"role": "user", "content": "Hello"}]
        response = adapter.chat(messages, model="gpt-4o")

        # Assertions
        assert isinstance(response, ChatResponse)
        assert response.content == "Test response from OpenAI"
        assert response.model == "gpt-4o"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 20
        assert response.usage["total_tokens"] == 30
        assert response.provider == "openai"
        assert response.cost is not None

    @patch("llm_connectivity.providers.openai_adapter.OpenAI")
    def test_chat_with_max_tokens(self, mock_openai_class):
        """Test chat with max_tokens parameter."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        adapter = OpenAIAdapter(api_key="sk-test123")
        adapter.client = mock_client

        messages = [{"role": "user", "content": "Hello"}]

        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.model = "gpt-4o"
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_client.chat.completions.create.return_value = mock_response

        adapter.chat(messages, model="gpt-4o", max_tokens=100)

        # Verify max_tokens was passed
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["max_tokens"] == 100

    @patch("llm_connectivity.providers.openai_adapter.OpenAI")
    def test_chat_rate_limit_error(self, mock_openai_class):
        """Test chat with rate limit error."""
        from openai import RateLimitError as OpenAIRateLimitError

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Create a mock RateLimitError (OpenAI SDK requires response and body)
        mock_response = Mock()
        mock_error = OpenAIRateLimitError("Rate limit exceeded", response=mock_response, body=None)
        mock_client.chat.completions.create.side_effect = mock_error

        adapter = OpenAIAdapter(api_key="sk-test123")
        adapter.client = mock_client

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(RateLimitError) as exc_info:
            adapter.chat(messages, model="gpt-4o")

        assert "rate limit" in str(exc_info.value).lower()
        assert exc_info.value.provider == "openai"


class TestOpenAIAdapterChatStream:
    """Test OpenAI streaming chat completion."""

    @patch("llm_connectivity.providers.openai_adapter.OpenAI")
    def test_chat_stream_success(self, mock_openai_class):
        """Test successful streaming chat completion."""
        # Setup mock stream
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Create mock chunks
        chunk1 = Mock()
        chunk1.choices = [Mock()]
        chunk1.choices[0].delta = Mock(content="Hello")
        chunk1.choices[0].finish_reason = None

        chunk2 = Mock()
        chunk2.choices = [Mock()]
        chunk2.choices[0].delta = Mock(content=" world")
        chunk2.choices[0].finish_reason = None

        chunk3 = Mock()
        chunk3.choices = [Mock()]
        chunk3.choices[0].delta = Mock(content=None)
        chunk3.choices[0].finish_reason = "stop"

        mock_client.chat.completions.create.return_value = iter([chunk1, chunk2, chunk3])

        adapter = OpenAIAdapter(api_key="sk-test123")
        adapter.client = mock_client

        messages = [{"role": "user", "content": "Hello"}]
        chunks = list(adapter.chat_stream(messages, model="gpt-4o"))

        # Verify chunks
        assert len(chunks) == 2  # Only chunks with content
        assert chunks[0].content == "Hello"
        assert chunks[1].content == " world"


class TestOpenAIAdapterEmbeddings:
    """Test OpenAI embeddings."""

    @patch("llm_connectivity.providers.openai_adapter.OpenAI")
    def test_embed_single_text(self, mock_openai_class, mock_openai_embedding_response):
        """Test embedding single text."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.embeddings.create.return_value = mock_openai_embedding_response

        adapter = OpenAIAdapter(api_key="sk-test123")
        adapter.client = mock_client

        response = adapter.embed("Hello world")

        assert isinstance(response, EmbeddingResponse)
        assert len(response.embeddings) == 2  # Mock has 2 embeddings
        assert response.embeddings[0] == [0.1, 0.2, 0.3]
        assert response.model == "text-embedding-3-small"
        assert response.usage["prompt_tokens"] == 5
        assert response.provider == "openai"

    @patch("llm_connectivity.providers.openai_adapter.OpenAI")
    def test_embed_multiple_texts(self, mock_openai_class, mock_openai_embedding_response):
        """Test embedding multiple texts (batch)."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.embeddings.create.return_value = mock_openai_embedding_response

        adapter = OpenAIAdapter(api_key="sk-test123")
        adapter.client = mock_client

        texts = ["Hello", "World"]
        response = adapter.embed(texts)

        # Verify batch processing
        call_kwargs = mock_client.embeddings.create.call_args[1]
        assert call_kwargs["input"] == texts
        assert len(response.embeddings) == 2


class TestOpenAIAdapterCostCalculation:
    """Test cost calculation."""

    def test_calculate_cost_gpt4o(self):
        """Test cost calculation for GPT-4o."""
        adapter = OpenAIAdapter(api_key="sk-test123")

        usage = {"prompt_tokens": 1000, "completion_tokens": 2000, "total_tokens": 3000}

        cost = adapter._calculate_cost(usage, "gpt-4o")

        # GPT-4o: $0.005 per 1K prompt, $0.015 per 1K completion
        expected = (1000 / 1000) * 0.005 + (2000 / 1000) * 0.015
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model."""
        adapter = OpenAIAdapter(api_key="sk-test123")

        usage = {"prompt_tokens": 1000, "completion_tokens": 2000, "total_tokens": 3000}

        cost = adapter._calculate_cost(usage, "unknown-model")
        assert cost is None


class TestOpenAIAdapterTokenEstimation:
    """Test token estimation."""

    def test_estimate_tokens(self):
        """Test token estimation for messages."""
        adapter = OpenAIAdapter(api_key="sk-test123")

        messages = [{"role": "user", "content": "Hello world this is a test"}]

        estimated = adapter._estimate_tokens(messages, "gpt-4o")

        # Should be > 0 (rough estimate based on char count)
        assert estimated > 0
        assert isinstance(estimated, int)


class TestOpenAIAdapterRepr:
    """Test __repr__ method."""

    def test_repr(self):
        """Test string representation."""
        adapter = OpenAIAdapter(api_key="sk-test123", timeout=30.0)
        repr_str = repr(adapter)

        assert "OpenAIAdapter" in repr_str
        assert "openai" in repr_str
        assert "30.0" in repr_str
