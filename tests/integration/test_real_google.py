"""
Integration Tests for Real Google AI API

Tests real Google Gemini API calls with cost control.
Estimated total cost: ~$0.03-0.05
"""

import pytest

from llm_connectivity.client import LLMClient
from llm_connectivity.errors import AuthenticationError, ValidationError


class TestGoogleRealChat:
    """Test real Google AI chat completion."""

    @pytest.mark.integration
    def test_chat_basic(self):
        """
        Test basic chat completion with real Google AI API.
        Estimated cost: ~$0.01
        """
        client = LLMClient(model="google/models/gemini-2.5-flash")
        response = client.chat(
            messages=[{"role": "user", "content": "Say 'test' only"}],
            max_tokens=5,
        )

        # Verify response structure
        assert response.content is not None
        assert len(response.content) > 0
        assert "gemini" in response.model.lower()
        assert response.provider == "google"

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
    def test_chat_with_system_message(self):
        """
        Test chat with system message (converted to prompt).
        Estimated cost: ~$0.01
        """
        client = LLMClient(model="google/models/gemini-2.5-flash")
        response = client.chat(
            messages=[
                {"role": "system", "content": "Be concise."},
                {"role": "user", "content": "Say 'ok'"},
            ],
            max_tokens=5,
        )

        assert response.content is not None
        assert response.cost < 0.01

    @pytest.mark.integration
    def test_chat_with_temperature(self):
        """
        Test chat with temperature parameter.
        Estimated cost: ~$0.01
        """
        client = LLMClient(model="google/models/gemini-2.5-flash")
        response = client.chat(
            messages=[{"role": "user", "content": "Say 'ok'"}],
            max_tokens=5,
            temperature=0.0,  # Deterministic
        )

        assert response.content is not None
        assert response.cost < 0.01


class TestGoogleRealErrorHandling:
    """Test real Google AI error scenarios."""

    @pytest.mark.integration
    def test_invalid_api_key_raises_authentication_error(self):
        """
        Test that invalid API key raises AuthenticationError.
        Estimated cost: $0.00 (fails before API call or immediately)
        """
        from llm_connectivity.providers.google_adapter import GoogleAdapter

        # Create adapter with invalid key
        adapter = GoogleAdapter(api_key="invalid-key-test")
        client = LLMClient(provider=adapter)

        # Should raise AuthenticationError (mapped from Google SDK)
        with pytest.raises((AuthenticationError, ValidationError)):
            # Google might raise different error types for invalid keys
            client.chat(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )

    @pytest.mark.integration
    def test_invalid_model_raises_error(self):
        """
        Test that invalid model name raises appropriate error.
        Estimated cost: $0.00 (fails validation)
        """
        from llm_connectivity.errors import ModelNotFoundError, ProviderError

        client = LLMClient(model="google/models/nonexistent-model-xyz")

        # Should raise error for non-existent model
        with pytest.raises((ModelNotFoundError, ProviderError, ValidationError)):
            client.chat(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )
