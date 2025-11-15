"""
Unit Tests for Anthropic Adapter

Tests Anthropic adapter functionality with mocked API responses.
Target: 95%+ coverage on anthropic_adapter.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from llm_connectivity.providers.anthropic_adapter import (
    AnthropicAdapter,
    ChatResponse,
    StreamChunk,
)
from llm_connectivity.errors import (
    RateLimitError,
    AuthenticationError,
    NetworkError,
    ModelNotFoundError,
)


class TestAnthropicAdapterInitialization:
    """Test AnthropicAdapter initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        adapter = AnthropicAdapter(api_key="sk-ant-test123")
        assert adapter.client is not None
        assert adapter.client.timeout == 60.0

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        adapter = AnthropicAdapter(api_key="sk-ant-test123", timeout=120.0)
        assert adapter.client.timeout == 120.0

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-env-key"})
    def test_init_from_env_var(self):
        """Test initialization from environment variable."""
        adapter = AnthropicAdapter()
        assert adapter.client is not None


class TestAnthropicAdapterChat:
    """Test Anthropic chat completion."""

    @patch("llm_connectivity.providers.anthropic_adapter.Anthropic")
    def test_chat_success(self, mock_anthropic_class, mock_anthropic_chat_response):
        """Test successful chat completion."""
        # Setup mock
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.return_value = mock_anthropic_chat_response

        # Create adapter
        adapter = AnthropicAdapter(api_key="sk-ant-test123")
        adapter.client = mock_client

        messages = [{"role": "user", "content": "Hello"}]
        response = adapter.chat(messages, model="claude-3-opus-20240229")

        # Assertions
        assert isinstance(response, ChatResponse)
        assert response.content == "Test response from Anthropic"
        assert response.model == "claude-3-opus-20240229"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 20
        assert response.provider == "anthropic"
        assert response.cost is not None

    @patch("llm_connectivity.providers.anthropic_adapter.Anthropic")
    def test_chat_with_max_tokens(self, mock_anthropic_class):
        """Test chat with max_tokens parameter (required by Anthropic)."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        adapter = AnthropicAdapter(api_key="sk-ant-test123")
        adapter.client = mock_client

        messages = [{"role": "user", "content": "Hello"}]

        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Response"
        mock_response.model = "claude-3-opus-20240229"
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)
        mock_client.messages.create.return_value = mock_response

        adapter.chat(messages, model="claude-3-opus-20240229", max_tokens=100)

        # Verify max_tokens was passed
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["max_tokens"] == 100

    @patch("llm_connectivity.providers.anthropic_adapter.Anthropic")
    def test_chat_rate_limit_error(self, mock_anthropic_class):
        """Test chat with rate limit error."""
        from anthropic import RateLimitError as AnthropicRateLimitError

        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Create mock error (Anthropic SDK requires response and body)
        mock_response = Mock()
        mock_error = AnthropicRateLimitError(
            "Rate limit exceeded", response=mock_response, body=None
        )
        mock_client.messages.create.side_effect = mock_error

        adapter = AnthropicAdapter(api_key="sk-ant-test123")
        adapter.client = mock_client

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(RateLimitError) as exc_info:
            adapter.chat(messages, model="claude-3-opus-20240229")

        assert "rate limit" in str(exc_info.value).lower()
        assert exc_info.value.provider == "anthropic"


class TestAnthropicAdapterChatStream:
    """Test Anthropic streaming chat completion."""

    @patch("llm_connectivity.providers.anthropic_adapter.Anthropic")
    def test_chat_stream_success(self, mock_anthropic_class):
        """Test successful streaming chat completion."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Create mock stream context manager
        mock_stream = MagicMock()
        mock_stream.__enter__.return_value = mock_stream
        mock_stream.__exit__.return_value = False
        mock_stream.text_stream = iter(["Hello", " ", "world"])

        mock_client.messages.stream.return_value = mock_stream

        adapter = AnthropicAdapter(api_key="sk-ant-test123")
        adapter.client = mock_client

        messages = [{"role": "user", "content": "Hello"}]
        chunks = list(adapter.chat_stream(messages, model="claude-3-opus-20240229"))

        # Verify chunks (3 content chunks + 1 final chunk)
        assert len(chunks) == 4
        assert chunks[0].content == "Hello"
        assert chunks[1].content == " "
        assert chunks[2].content == "world"
        assert chunks[3].finish_reason == "end_turn"


class TestAnthropicAdapterCostCalculation:
    """Test cost calculation."""

    def test_calculate_cost_claude_3_opus(self):
        """Test cost calculation for Claude 3 Opus."""
        adapter = AnthropicAdapter(api_key="sk-ant-test123")

        usage = {
            "prompt_tokens": 1_000_000,
            "completion_tokens": 1_000_000,
            "total_tokens": 2_000_000,
        }

        cost = adapter._calculate_cost(usage, "claude-3-opus-20240229")

        # Claude 3 Opus: $15 per 1M prompt, $75 per 1M completion
        expected = (1_000_000 / 1_000_000) * 15 + (1_000_000 / 1_000_000) * 75
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model."""
        adapter = AnthropicAdapter(api_key="sk-ant-test123")

        usage = {"prompt_tokens": 1000, "completion_tokens": 2000, "total_tokens": 3000}

        cost = adapter._calculate_cost(usage, "unknown-model")
        assert cost is None


class TestAnthropicAdapterTokenEstimation:
    """Test token estimation."""

    def test_estimate_tokens(self):
        """Test token estimation for messages."""
        adapter = AnthropicAdapter(api_key="sk-ant-test123")

        messages = [{"role": "user", "content": "Hello world this is a test"}]

        estimated = adapter._estimate_tokens(messages, "claude-3-opus-20240229")

        # Should be > 0 (rough estimate based on char count)
        assert estimated > 0
        assert isinstance(estimated, int)


class TestAnthropicAdapterRepr:
    """Test __repr__ method."""

    def test_repr(self):
        """Test string representation."""
        adapter = AnthropicAdapter(api_key="sk-ant-test123", timeout=30.0)
        repr_str = repr(adapter)

        assert "AnthropicAdapter" in repr_str
        assert "anthropic" in repr_str
        assert "30.0" in repr_str
