"""
Unit Tests for Google Adapter

Tests Google AI adapter functionality with mocked API responses.
Target: 95%+ coverage on google_adapter.py
Note: Google API has different structure than OpenAI/Anthropic
"""

from unittest.mock import Mock, patch

import pytest

from llm_connectivity.providers.google_adapter import (
    ChatResponse,
    EmbeddingResponse,
    GoogleAdapter,
)


class TestGoogleAdapterInitialization:
    """Test GoogleAdapter initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            adapter = GoogleAdapter(api_key="test-key-123")
            assert adapter.timeout == 60.0

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            adapter = GoogleAdapter(api_key="test-key-123", timeout=120.0)
            assert adapter.timeout == 120.0

    @patch.dict("os.environ", {"GOOGLE_AI_API_KEY": "env-key"})
    def test_init_from_env_var(self):
        """Test initialization from environment variable."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            adapter = GoogleAdapter()
            assert adapter.timeout == 60.0

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_api_key_raises_error(self):
        """Test initialization without API key raises ValueError."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            with pytest.raises(ValueError, match="GOOGLE_AI_API_KEY not set"):
                GoogleAdapter()


class TestGoogleAdapterMessageConversion:
    """Test message to prompt conversion."""

    def test_messages_to_prompt_single_user(self):
        """Test converting single user message."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            adapter = GoogleAdapter(api_key="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            prompt = adapter._messages_to_prompt(messages)
            assert "User: Hello" in prompt

    def test_messages_to_prompt_with_system(self):
        """Test converting messages with system message."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            adapter = GoogleAdapter(api_key="test-key")
            messages = [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello"},
            ]
            prompt = adapter._messages_to_prompt(messages)
            assert "You are helpful" in prompt
            assert "User: Hello" in prompt

    def test_messages_to_prompt_with_assistant(self):
        """Test converting messages with assistant message."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            adapter = GoogleAdapter(api_key="test-key")
            messages = [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello!"},
            ]
            prompt = adapter._messages_to_prompt(messages)
            assert "User: Hi" in prompt
            assert "Assistant: Hello!" in prompt


class TestGoogleAdapterChat:
    """Test Google chat completion."""

    @patch("llm_connectivity.providers.google_adapter.genai.GenerativeModel")
    def test_chat_success(self, mock_model_class, mock_google_chat_response):
        """Test successful chat completion."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            # Setup mock
            mock_model = Mock()
            mock_model_class.return_value = mock_model
            mock_model.generate_content.return_value = mock_google_chat_response

            adapter = GoogleAdapter(api_key="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            response = adapter.chat(messages, model="models/gemini-2.5-pro")

            # Assertions
            assert isinstance(response, ChatResponse)
            assert response.content == "Test response from Google"
            assert response.model == "models/gemini-2.5-pro"
            assert response.provider == "google"
            assert response.usage["prompt_tokens"] > 0
            assert response.cost is not None

    @patch("llm_connectivity.providers.google_adapter.genai.GenerativeModel")
    def test_chat_blocked_by_safety_filters(self, mock_model_class):
        """Test chat blocked by safety filters."""
        from unittest.mock import PropertyMock

        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            mock_model = Mock()
            mock_model_class.return_value = mock_model

            # Mock blocked response with PropertyMock for .text attribute
            mock_response = Mock()
            type(mock_response).text = PropertyMock(side_effect=ValueError("blocked"))

            # Create properly configured candidate mock
            mock_candidate = Mock()
            mock_candidate.finish_reason = "SAFETY"
            mock_response.candidates = [mock_candidate]

            mock_model.generate_content.return_value = mock_response

            adapter = GoogleAdapter(api_key="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            response = adapter.chat(messages, model="models/gemini-2.5-pro")

            # Should return blocked message
            assert "[Response blocked by Google safety filters" in response.content

    @patch("llm_connectivity.providers.google_adapter.genai.GenerativeModel")
    def test_chat_with_max_tokens(self, mock_model_class, mock_google_chat_response):
        """Test chat with max_tokens parameter."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            mock_model = Mock()
            mock_model_class.return_value = mock_model
            mock_model.generate_content.return_value = mock_google_chat_response

            adapter = GoogleAdapter(api_key="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            adapter.chat(messages, model="models/gemini-2.5-pro", max_tokens=100)

            # Verify max_tokens was passed as max_output_tokens
            call_kwargs = mock_model.generate_content.call_args[1]
            assert call_kwargs["generation_config"]["max_output_tokens"] == 100


class TestGoogleAdapterChatStream:
    """Test Google streaming chat completion."""

    @patch("llm_connectivity.providers.google_adapter.genai.GenerativeModel")
    def test_chat_stream_success(self, mock_model_class):
        """Test successful streaming chat completion."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            mock_model = Mock()
            mock_model_class.return_value = mock_model

            # Create mock chunks
            chunk1 = Mock()
            chunk1.text = "Hello"

            chunk2 = Mock()
            chunk2.text = " world"

            mock_model.generate_content.return_value = iter([chunk1, chunk2])

            adapter = GoogleAdapter(api_key="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            chunks = list(adapter.chat_stream(messages, model="models/gemini-2.5-pro"))

            # Verify chunks (2 content + 1 final)
            assert len(chunks) == 3
            assert chunks[0].content == "Hello"
            assert chunks[1].content == " world"
            assert chunks[2].finish_reason == "stop"

    @patch("llm_connectivity.providers.google_adapter.genai.GenerativeModel")
    def test_chat_stream_with_max_tokens(self, mock_model_class):
        """Test streaming with max_tokens parameter."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            mock_model = Mock()
            mock_model_class.return_value = mock_model

            chunk1 = Mock()
            chunk1.text = "Test"
            mock_model.generate_content.return_value = iter([chunk1])

            adapter = GoogleAdapter(api_key="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            list(adapter.chat_stream(messages, model="models/gemini-2.5-pro", max_tokens=50))

            # Verify max_tokens was passed
            call_kwargs = mock_model.generate_content.call_args[1]
            assert call_kwargs["generation_config"]["max_output_tokens"] == 50


class TestGoogleAdapterEmbeddings:
    """Test Google embeddings."""

    @patch("llm_connectivity.providers.google_adapter.genai.embed_content")
    def test_embed_single_text(self, mock_embed):
        """Test embedding single text."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            # Mock single embedding response (flat list)
            mock_embed.return_value = {"embedding": [0.1, 0.2, 0.3]}

            adapter = GoogleAdapter(api_key="test-key")
            response = adapter.embed("Hello world")

            assert isinstance(response, EmbeddingResponse)
            assert len(response.embeddings) == 1
            assert response.embeddings[0] == [0.1, 0.2, 0.3]
            assert response.provider == "google"

    @patch("llm_connectivity.providers.google_adapter.genai.embed_content")
    def test_embed_multiple_texts(self, mock_embed):
        """Test embedding multiple texts (batch)."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            # Mock batch embedding response (list of lists)
            mock_embed.return_value = {"embedding": [[0.1, 0.2], [0.3, 0.4]]}

            adapter = GoogleAdapter(api_key="test-key")
            texts = ["Hello", "World"]
            response = adapter.embed(texts)

            assert len(response.embeddings) == 2
            assert response.embeddings[0] == [0.1, 0.2]
            assert response.embeddings[1] == [0.3, 0.4]

    @patch("llm_connectivity.providers.google_adapter.genai.embed_content")
    def test_embed_empty_result(self, mock_embed):
        """Test embedding with empty result."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            # Mock empty embedding response
            mock_embed.return_value = {"embedding": []}

            adapter = GoogleAdapter(api_key="test-key")
            response = adapter.embed("Test text")

            assert len(response.embeddings) == 0
            assert response.provider == "google"


class TestGoogleAdapterCostCalculation:
    """Test cost calculation."""

    def test_calculate_cost_gemini_2_5_pro(self):
        """Test cost calculation for Gemini 2.5 Pro."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            adapter = GoogleAdapter(api_key="test-key")

            usage = {
                "prompt_tokens": 1_000_000,
                "completion_tokens": 1_000_000,
                "total_tokens": 2_000_000,
            }

            cost = adapter._calculate_cost(usage, "models/gemini-2.5-pro")

            # Gemini 2.5 Pro: $1.25 per 1M prompt, $5.00 per 1M completion
            expected = (1_000_000 / 1_000_000) * 1.25 + (1_000_000 / 1_000_000) * 5.00
            assert cost == pytest.approx(expected, rel=1e-6)

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            adapter = GoogleAdapter(api_key="test-key")

            usage = {"prompt_tokens": 1000, "completion_tokens": 2000, "total_tokens": 3000}
            cost = adapter._calculate_cost(usage, "unknown-model")
            assert cost is None


class TestGoogleAdapterEmbeddingCostCalculation:
    """Test embedding cost calculation."""

    def test_calculate_embedding_cost_unknown_model(self):
        """Test embedding cost calculation for unknown model returns None."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            adapter = GoogleAdapter(api_key="test-key")

            usage = {"prompt_tokens": 1000, "total_tokens": 1000}
            cost = adapter._calculate_embedding_cost(usage, "models/unknown-embedding-model")
            assert cost is None


class TestGoogleAdapterTokenEstimation:
    """Test token estimation."""

    def test_estimate_tokens(self):
        """Test token estimation."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            adapter = GoogleAdapter(api_key="test-key")
            text = "Hello world this is a test"
            estimated = adapter._estimate_tokens(text)

            # Should be > 0 (rough estimate: ~4 chars per token)
            assert estimated > 0
            assert isinstance(estimated, int)


class TestGoogleAdapterRepr:
    """Test __repr__ method."""

    def test_repr(self):
        """Test string representation."""
        with patch("llm_connectivity.providers.google_adapter.genai.configure"):
            adapter = GoogleAdapter(api_key="test-key", timeout=30.0)
            repr_str = repr(adapter)

            assert "GoogleAdapter" in repr_str
            assert "google" in repr_str
            assert "30.0" in repr_str
