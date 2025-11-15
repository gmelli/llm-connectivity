"""
Integration Tests for Real OpenAI API

Tests real OpenAI API calls with cost control.
Estimated total cost: ~$0.05-0.10
"""

import pytest

from llm_connectivity.client import LLMClient
from llm_connectivity.errors import AuthenticationError


class TestOpenAIRealChat:
    """Test real OpenAI chat completion."""

    @pytest.mark.integration
    def test_chat_basic(self):
        """
        Test basic chat completion with real OpenAI API.
        Estimated cost: ~$0.01
        """
        client = LLMClient(model="openai/gpt-4o-mini")
        response = client.chat(
            messages=[{"role": "user", "content": "Say 'test' only"}],
            max_tokens=5,
        )

        # Verify response structure
        assert response.content is not None
        assert len(response.content) > 0
        assert response.model == "gpt-4o-mini-2024-07-18" or "gpt-4o-mini" in response.model
        assert response.provider == "openai"

        # Verify usage tracking
        assert response.usage is not None
        assert response.usage["prompt_tokens"] > 0
        assert response.usage["completion_tokens"] > 0
        assert response.usage["total_tokens"] > 0

        # Verify cost calculation
        assert response.cost is not None
        assert response.cost > 0
        assert response.cost < 0.01  # Should be very cheap

    @pytest.mark.integration
    def test_chat_with_temperature(self):
        """
        Test chat with temperature parameter.
        Estimated cost: ~$0.01
        """
        client = LLMClient(model="openai/gpt-4o-mini")
        response = client.chat(
            messages=[{"role": "user", "content": "Say 'ok'"}],
            max_tokens=5,
            temperature=0.0,  # Deterministic
        )

        assert response.content is not None
        assert response.cost < 0.01


class TestOpenAIRealStreaming:
    """Test real OpenAI streaming."""

    @pytest.mark.integration
    def test_streaming_basic(self):
        """
        Test streaming chat completion.
        Estimated cost: ~$0.01
        """
        client = LLMClient(model="openai/gpt-4o-mini")
        chunks = list(
            client.chat_stream(
                messages=[{"role": "user", "content": "Count to 3"}],
                max_tokens=15,
            )
        )

        # Verify streaming worked
        assert len(chunks) > 0, "Should receive multiple chunks"

        # Verify chunks have content
        content = "".join(chunk.content for chunk in chunks if chunk.content)
        assert len(content) > 0, "Should have non-empty content"

        # Verify raw chunks are available
        assert all(chunk.raw_chunk is not None for chunk in chunks)


class TestOpenAIRealErrorHandling:
    """Test real OpenAI error scenarios."""

    @pytest.mark.integration
    def test_invalid_api_key_raises_authentication_error(self):
        """
        Test that invalid API key raises AuthenticationError.
        Estimated cost: $0.00 (fails before API call)
        """
        from llm_connectivity.providers.openai_adapter import OpenAIAdapter

        # Create adapter with invalid key
        adapter = OpenAIAdapter(api_key="sk-invalid-key-test")
        client = LLMClient(provider=adapter)

        # Should raise AuthenticationError (mapped from OpenAI SDK)
        with pytest.raises(AuthenticationError):
            client.chat(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )

    @pytest.mark.integration
    def test_excessive_tokens_raises_validation_error(self):
        """
        Test that excessive token request raises appropriate error.
        Estimated cost: $0.00 (fails validation)
        """
        from llm_connectivity.errors import ContextWindowExceededError, ValidationError

        client = LLMClient(model="openai/gpt-4o-mini")

        # Request more tokens than model supports (should fail)
        with pytest.raises((ValidationError, ContextWindowExceededError)):
            client.chat(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=200000,  # Way over gpt-4o-mini limit
            )
