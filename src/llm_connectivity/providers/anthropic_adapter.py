"""
Anthropic Chat API Adapter

Pattern: 99% OpenAI compatible (L002 research finding)
Purpose: Provider-specific implementation following OpenAI patterns

Key Features:
1. Pre + post token tracking (Anthropic's superior approach - L002)
2. Cost calculation hooks
3. Streaming support (context manager → simple iterator abstraction)
4. Error mapping to unified hierarchy
5. Retry logic with differentiated backoff

Differences from OpenAI:
- Context manager streaming (async with) vs OpenAI's simple iterator
- Superior token tracking (pre + post built-in)
- Different model names (claude-3-opus vs gpt-4)
- Anthropic-specific headers (anthropic-version, anthropic-beta)

Design Principles:
- Keep wrapper thin (delegate to official SDK)
- Abstract context manager streaming to simple iterator
- Leverage Anthropic's built-in token tracking (superior to OpenAI)
- Map all exceptions to unified hierarchy
"""
import os
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass

from anthropic import Anthropic

from llm_connectivity.errors import map_anthropic_exception, LLMError
from llm_connectivity.retry import retry_with_backoff


@dataclass
class ChatResponse:
    """Unified chat response format (same as OpenAI adapter)."""
    content: str
    model: str
    usage: Dict[str, int]  # {prompt_tokens, completion_tokens, total_tokens}
    cost: Optional[float]
    provider: str = "anthropic"
    raw_response: Optional[Any] = None


@dataclass
class StreamChunk:
    """Streaming response chunk (same as OpenAI adapter)."""
    content: str
    finish_reason: Optional[str] = None
    raw_chunk: Optional[Any] = None


class AnthropicAdapter:
    """Anthropic Chat API adapter with unified interface.

    Usage:
        # Basic usage
        adapter = AnthropicAdapter(api_key="sk-ant-...")
        response = adapter.chat(
            messages=[{"role": "user", "content": "Hello"}],
            model="claude-3-opus-20240229"
        )

        # Streaming
        for chunk in adapter.chat_stream(messages=[...], model="claude-3-opus"):
            print(chunk.content, end="")
    """

    # Pricing per 1M tokens (as of 2025-11-14)
    # Source: https://www.anthropic.com/pricing
    PRICING = {
        "claude-3-opus-20240229": {"prompt": 15.00, "completion": 75.00},
        "claude-3-sonnet-20240229": {"prompt": 3.00, "completion": 15.00},
        "claude-3-haiku-20240307": {"prompt": 0.25, "completion": 1.25},
        # Claude 3.5 models (if API key has access)
        "claude-3-5-sonnet-20240620": {"prompt": 3.00, "completion": 15.00},
        "claude-3-5-sonnet-20241022": {"prompt": 3.00, "completion": 15.00},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3
    ):
        """Initialize Anthropic adapter.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            base_url: Custom API base URL (for proxies)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts (handled by SDK)

        Note: Retry logic is applied via @retry_with_backoff decorator on methods
        """
        self.client = Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            base_url=base_url,
            timeout=timeout,
            max_retries=0  # We handle retries ourselves via decorator
        )

    def _estimate_tokens(self, messages: List[Dict[str, str]], model: str) -> int:
        """Estimate token count for messages (pre-request).

        Simple heuristic: ~4 chars per token (rough approximation)

        TODO: Use Anthropic's count_tokens API for accurate counting (production)

        Args:
            messages: Chat messages
            model: Model name

        Returns:
            Estimated token count
        """
        text = " ".join(msg.get("content", "") for msg in messages)
        # Rough estimate: 4 chars per token + overhead for message formatting
        char_count = len(text)
        return (char_count // 4) + (len(messages) * 10)  # +10 tokens per message for overhead

    def _calculate_cost(self, usage: Dict[str, int], model: str) -> Optional[float]:
        """Calculate cost for request.

        Args:
            usage: Token usage dict {prompt_tokens, completion_tokens, total_tokens}
            model: Model name

        Returns:
            Cost in USD, or None if pricing unavailable
        """
        # Normalize model name (handle versioned models)
        base_model = model
        for known_model in self.PRICING.keys():
            if known_model in model:
                base_model = known_model
                break

        pricing = self.PRICING.get(base_model)
        if not pricing:
            return None

        # Anthropic pricing is per 1M tokens, not 1K like OpenAI
        prompt_cost = (usage["prompt_tokens"] / 1_000_000) * pricing["prompt"]
        completion_cost = (usage["completion_tokens"] / 1_000_000) * pricing["completion"]

        return prompt_cost + completion_cost

    @retry_with_backoff
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-opus-20240229",
        max_tokens: int = 1024,  # Anthropic requires max_tokens (no optional)
        temperature: float = 1.0,
        **kwargs
    ) -> ChatResponse:
        """Send chat completion request.

        Args:
            messages: Chat messages [{"role": "user", "content": "..."}]
            model: Model name (e.g., "claude-3-opus", "claude-3-sonnet")
            max_tokens: Maximum completion tokens (REQUIRED by Anthropic)
            temperature: Sampling temperature (0-1, note: Anthropic uses 0-1 not 0-2)
            **kwargs: Additional parameters passed to Anthropic API

        Returns:
            ChatResponse with unified format

        Raises:
            LLMError: On API errors (mapped to unified hierarchy)

        Note: Anthropic has superior token tracking (pre + post built-in)
        """
        # Pre-request token estimation
        estimated_tokens = self._estimate_tokens(messages, model)
        print(f"  Estimated prompt tokens: {estimated_tokens}")

        try:
            # Call Anthropic API
            response = self.client.messages.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            # Extract response
            content = response.content[0].text

            # Post-request token actuals (from API response)
            # Anthropic provides both input and output tokens (superior to OpenAI)
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }

            # Calculate cost
            cost = self._calculate_cost(usage, model)

            return ChatResponse(
                content=content,
                model=response.model,
                usage=usage,
                cost=cost,
                provider="anthropic",
                raw_response=response
            )

        except Exception as e:
            # Map to unified exception hierarchy
            raise map_anthropic_exception(e)

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-opus-20240229",
        max_tokens: int = 1024,
        temperature: float = 1.0,
        **kwargs
    ) -> Iterator[StreamChunk]:
        """Send streaming chat completion request.

        Args:
            messages: Chat messages
            model: Model name
            max_tokens: Maximum completion tokens
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Yields:
            StreamChunk for each delta

        Raises:
            LLMError: On API errors (mapped to unified hierarchy)

        Note: Abstracts Anthropic's context manager to simple iterator (L002 pattern)
        """
        # Pre-request token estimation
        estimated_tokens = self._estimate_tokens(messages, model)
        print(f"  Estimated prompt tokens: {estimated_tokens}")

        try:
            # Call Anthropic streaming API (uses context manager)
            with self.client.messages.stream(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            ) as stream:
                # Abstract context manager to simple iterator
                for text in stream.text_stream:
                    yield StreamChunk(
                        content=text,
                        finish_reason=None,
                        raw_chunk=None
                    )

                # Final chunk with finish reason
                yield StreamChunk(
                    content="",
                    finish_reason="end_turn",  # Anthropic terminology
                    raw_chunk=None
                )

        except Exception as e:
            # Map to unified exception hierarchy
            raise map_anthropic_exception(e)

    def __repr__(self) -> str:
        """Return string representation of AnthropicAdapter.

        Returns:
            String representation showing provider and timeout configuration.

        Example:
            >>> adapter = AnthropicAdapter(timeout=30.0)
            >>> print(repr(adapter))
            AnthropicAdapter(model=anthropic, timeout=30.0)
        """
        return f"AnthropicAdapter(model=anthropic, timeout={self.client.timeout})"
