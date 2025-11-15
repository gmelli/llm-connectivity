"""
Integration Tests for Provider Switching

Tests the CORE VALUE PROPOSITION: switching providers requires only changing the model string.
Estimated cost per test: ~$0.01-0.02 (ultra-minimal tokens)
Total estimated cost: ~$0.02-0.04
"""

import os
import pytest
from llm_connectivity.client import LLMClient


class TestProviderSwitching:
    """Test that provider switching requires only changing the model string."""

    def _test_chat_with_model(self, model: str) -> None:
        """
        Reusable test function - IDENTICAL code for all providers.
        Only the model parameter changes.
        """
        client = LLMClient(model=model)
        response = client.chat(
            messages=[{"role": "user", "content": "Say 'ok' only"}],
            max_tokens=5,  # Ultra-minimal for cost control
        )

        # Verify response
        assert response.content is not None
        assert len(response.content) > 0
        assert response.model is not None
        assert response.usage is not None
        assert response.cost is not None

    @pytest.mark.integration
    def test_switching_openai_to_google(self):
        """
        Test switching from OpenAI to Google - SAME CODE, different model string.
        This is a <1 line change (just the model parameter).
        Estimated cost: ~$0.02
        """
        # Test with OpenAI
        self._test_chat_with_model("openai/gpt-4o-mini")

        # Test with Google - IDENTICAL code, just model string changed
        self._test_chat_with_model("google/models/gemini-2.5-flash")

        # ✅ PROOF: Same function, same code, different provider
        # This demonstrates <5 line switching (actually <1 line!)

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
    def test_switching_to_anthropic(self):
        """
        Test switching to Anthropic - SAME CODE, different model string.
        Estimated cost: ~$0.01
        """
        # Test with Anthropic - IDENTICAL code as above
        self._test_chat_with_model("anthropic/claude-3-haiku-20240307")

        # ✅ PROOF: Works with Anthropic using same code pattern


class TestProviderSwitchingStreaming:
    """Test provider switching with streaming responses."""

    def _test_streaming_with_model(self, model: str) -> None:
        """
        Reusable streaming test - IDENTICAL code for all providers.
        Only the model parameter changes.
        """
        client = LLMClient(model=model)
        chunks = list(
            client.chat_stream(
                messages=[{"role": "user", "content": "Say 'hi' only"}],
                max_tokens=10,  # Slightly higher for reliable streaming
            )
        )

        # Verify streaming works
        assert len(chunks) > 0, "Should receive at least one chunk"
        content = "".join(chunk.content for chunk in chunks if chunk.content)
        assert len(content) > 0, "Should receive non-empty content across chunks"

    @pytest.mark.integration
    def test_streaming_openai(self):
        """
        Test streaming with OpenAI - validates streaming functionality.
        Estimated cost: ~$0.01
        """
        # Test streaming with OpenAI (most reliable streaming implementation)
        self._test_streaming_with_model("openai/gpt-4o-mini")

        # ✅ PROOF: Streaming works with same code pattern

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
    def test_streaming_anthropic(self):
        """
        Test streaming with Anthropic - SAME CODE pattern.
        Estimated cost: ~$0.01
        """
        # Test streaming with Anthropic - IDENTICAL code
        self._test_streaming_with_model("anthropic/claude-3-haiku-20240307")

        # ✅ PROOF: Anthropic streaming uses same code pattern
