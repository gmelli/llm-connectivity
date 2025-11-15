"""
Unit Tests for LLM Client Interface

Tests unified client interface with mocked provider adapters.
Target: 95%+ coverage on client.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from llm_connectivity.client import LLMClient, ChatResponse, StreamChunk, EmbeddingResponse
from llm_connectivity.providers.openai_adapter import OpenAIAdapter
from llm_connectivity.providers.anthropic_adapter import AnthropicAdapter
from llm_connectivity.providers.google_adapter import GoogleAdapter


class TestLLMClientInitialization:
    """Test LLMClient initialization."""

    def test_init_with_model_string_openai(self):
        """Test initialization with OpenAI model string."""
        with patch("llm_connectivity.client.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter

            client = LLMClient(model="openai/gpt-4o")

            assert client.model == "openai/gpt-4o"
            assert client.provider == mock_adapter
            mock_adapter_class.assert_called_once()

    def test_init_with_model_string_anthropic(self):
        """Test initialization with Anthropic model string."""
        with patch("llm_connectivity.client.AnthropicAdapter") as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter

            client = LLMClient(model="anthropic/claude-3-opus-20240229")

            assert client.model == "anthropic/claude-3-opus-20240229"
            assert client.provider == mock_adapter

    def test_init_with_model_string_google(self):
        """Test initialization with Google model string."""
        with patch("llm_connectivity.client.GoogleAdapter") as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter

            client = LLMClient(model="google/gemini-2.5-pro")

            assert client.model == "google/gemini-2.5-pro"
            assert client.provider == mock_adapter

    def test_init_with_provider_object(self):
        """Test initialization with provider object."""
        mock_provider = Mock(spec=OpenAIAdapter)
        client = LLMClient(provider=mock_provider)

        assert client.provider == mock_provider
        assert client.model is None  # Model specified per-request

    def test_init_with_kwargs_passed_to_provider(self):
        """Test that kwargs are passed to provider adapter."""
        with patch("llm_connectivity.client.OpenAIAdapter") as mock_adapter_class:
            client = LLMClient(model="openai/gpt-4o", timeout=120, max_retries=5)

            mock_adapter_class.assert_called_once_with(timeout=120, max_retries=5)

    def test_init_without_model_or_provider_raises_error(self):
        """Test initialization without model or provider raises ValueError."""
        with pytest.raises(ValueError, match="Must specify either 'model' or 'provider'"):
            LLMClient()

    def test_init_with_invalid_model_format_raises_error(self):
        """Test initialization with invalid model format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid model string format"):
            LLMClient(model="gpt-4o")  # Missing provider prefix

    def test_init_with_unsupported_provider_raises_error(self):
        """Test initialization with unsupported provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMClient(model="cohere/command")


class TestLLMClientChat:
    """Test LLM client chat completion."""

    def test_chat_with_model_string_client(self):
        """Test chat with model string initialized client."""
        # Create mock response directly
        mock_response = ChatResponse(
            content="Test response",
            model="gpt-4o",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            cost=0.001,
            provider="openai",
        )

        with patch("llm_connectivity.client.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter
            mock_adapter.chat.return_value = mock_response

            client = LLMClient(model="openai/gpt-4o")
            messages = [{"role": "user", "content": "Hello"}]
            response = client.chat(messages)

            assert response.content == "Test response"
            mock_adapter.chat.assert_called_once_with(
                messages=messages,
                model="gpt-4o",  # Extracted from "openai/gpt-4o"
                max_tokens=None,
                temperature=1.0,
            )

    def test_chat_with_provider_object_client(self):
        """Test chat with provider object initialized client."""
        mock_response = ChatResponse(
            content="Test response",
            model="gpt-4o",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            cost=0.001,
            provider="openai",
        )

        mock_provider = Mock(spec=OpenAIAdapter)
        mock_provider.chat.return_value = mock_response

        client = LLMClient(provider=mock_provider)
        messages = [{"role": "user", "content": "Hello"}]
        response = client.chat(messages, model="gpt-4o")

        assert response.content == "Test response"
        mock_provider.chat.assert_called_once_with(
            messages=messages,
            model="gpt-4o",
            max_tokens=None,
            temperature=1.0,
        )

    def test_chat_with_model_override(self, mock_openai_chat_response):
        """Test chat with model parameter overriding client model."""
        with patch("llm_connectivity.client.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter
            mock_adapter.chat.return_value = mock_openai_chat_response

            client = LLMClient(model="openai/gpt-4o")
            messages = [{"role": "user", "content": "Hello"}]
            response = client.chat(messages, model="openai/gpt-3.5-turbo")

            # Should use gpt-3.5-turbo, not gpt-4o
            mock_adapter.chat.assert_called_once_with(
                messages=messages,
                model="gpt-3.5-turbo",
                max_tokens=None,
                temperature=1.0,
            )

    def test_chat_with_parameters(self, mock_openai_chat_response):
        """Test chat with max_tokens and temperature."""
        with patch("llm_connectivity.client.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter
            mock_adapter.chat.return_value = mock_openai_chat_response

            client = LLMClient(model="openai/gpt-4o")
            messages = [{"role": "user", "content": "Hello"}]
            client.chat(messages, max_tokens=100, temperature=0.5)

            mock_adapter.chat.assert_called_once_with(
                messages=messages,
                model="gpt-4o",
                max_tokens=100,
                temperature=0.5,
            )


class TestLLMClientChatStream:
    """Test LLM client streaming chat completion."""

    def test_chat_stream_success(self):
        """Test successful streaming chat completion."""
        with patch("llm_connectivity.client.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter

            # Create mock stream chunks
            chunk1 = StreamChunk(content="Hello")
            chunk2 = StreamChunk(content=" world")
            chunk3 = StreamChunk(content="", finish_reason="stop")
            mock_adapter.chat_stream.return_value = iter([chunk1, chunk2, chunk3])

            client = LLMClient(model="openai/gpt-4o")
            messages = [{"role": "user", "content": "Hello"}]
            chunks = list(client.chat_stream(messages))

            assert len(chunks) == 3
            assert chunks[0].content == "Hello"
            assert chunks[1].content == " world"
            assert chunks[2].finish_reason == "stop"


class TestLLMClientEmbed:
    """Test LLM client embeddings."""

    def test_embed_single_text(self):
        """Test embedding single text."""
        mock_response = EmbeddingResponse(
            embeddings=[[0.1, 0.2, 0.3]],
            model="text-embedding-3-small",
            usage={"prompt_tokens": 5, "total_tokens": 5},
            cost=0.0001,
            provider="openai",
        )

        with patch("llm_connectivity.client.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter
            mock_adapter.embed.return_value = mock_response

            client = LLMClient(model="openai/text-embedding-3-small")
            response = client.embed("Hello world")

            assert len(response.embeddings) == 1
            mock_adapter.embed.assert_called_once_with(
                texts="Hello world", model="text-embedding-3-small"
            )

    def test_embed_multiple_texts(self):
        """Test embedding multiple texts (batch)."""
        mock_response = EmbeddingResponse(
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            model="text-embedding-3-small",
            usage={"prompt_tokens": 10, "total_tokens": 10},
            cost=0.0002,
            provider="openai",
        )

        with patch("llm_connectivity.client.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter
            mock_adapter.embed.return_value = mock_response

            client = LLMClient(model="openai/text-embedding-3-small")
            texts = ["Hello", "World"]
            response = client.embed(texts)

            assert len(response.embeddings) == 2
            mock_adapter.embed.assert_called_once_with(texts=texts, model="text-embedding-3-small")

    def test_embed_with_model_override(self, mock_openai_embedding_response):
        """Test embedding with model parameter override."""
        with patch("llm_connectivity.client.OpenAIAdapter") as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter
            mock_adapter.embed.return_value = mock_openai_embedding_response

            client = LLMClient(model="openai/text-embedding-3-small")
            client.embed("Test", model="openai/text-embedding-3-large")

            # Should use text-embedding-3-large
            mock_adapter.embed.assert_called_once_with(texts="Test", model="text-embedding-3-large")

    def test_embed_with_no_model_uses_default(self, mock_openai_embedding_response):
        """Test embedding without model uses provider default."""
        mock_provider = Mock(spec=OpenAIAdapter)
        mock_provider.embed.return_value = mock_openai_embedding_response

        client = LLMClient(provider=mock_provider)
        client.embed("Test")

        # Should call without model parameter (provider uses default)
        mock_provider.embed.assert_called_once_with(texts="Test")

    def test_embed_with_unsupported_provider_raises_error(self):
        """Test embedding with provider that doesn't support embeddings."""
        # Anthropic doesn't have embed method
        mock_provider = Mock(spec=AnthropicAdapter)
        # Remove embed attribute to simulate unsupported feature
        delattr(mock_provider, "embed")

        client = LLMClient(provider=mock_provider)

        with pytest.raises(AttributeError, match="does not support embeddings"):
            client.embed("Test")


class TestLLMClientRepr:
    """Test __repr__ method."""

    def test_repr_with_model_string(self):
        """Test string representation with model string."""
        with patch("llm_connectivity.client.OpenAIAdapter"):
            client = LLMClient(model="openai/gpt-4o")
            repr_str = repr(client)

            assert "LLMClient" in repr_str
            assert "openai/gpt-4o" in repr_str

    def test_repr_with_provider_object(self):
        """Test string representation with provider object."""
        mock_provider = Mock(spec=OpenAIAdapter)
        client = LLMClient(provider=mock_provider)
        repr_str = repr(client)

        assert "LLMClient" in repr_str
        assert "model=None" in repr_str
