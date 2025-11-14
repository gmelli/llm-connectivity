"""
OpenAI Chat API Adapter

Pattern: Thin wrapper around official SDK (L002 research finding)
Purpose: Provider-specific implementation with unified interface

Key Features:
1. Pre + post token tracking (Anthropic pattern - L002)
2. Cost calculation hooks
3. Streaming support (simple iterator)
4. Error mapping to unified hierarchy
5. Retry logic with differentiated backoff

Design Principles:
- Keep wrapper thin (delegate to official SDK)
- Track tokens before AND after (Anthropic's superior approach)
- Simple streaming (iterator, not context manager)
- Map all exceptions to unified hierarchy
"""
import os
from typing import List, Dict, Any, Optional, Iterator, Union
from dataclasses import dataclass

from openai import OpenAI

from llm_connectivity.errors import map_openai_exception, LLMError
from llm_connectivity.retry import retry_with_backoff


@dataclass
class ChatResponse:
    """Unified chat response format.

    Attributes:
        content: Response text
        model: Model used
        usage: Token usage statistics
        cost: Estimated cost (USD)
        provider: Provider name
        raw_response: Original provider response
    """
    content: str
    model: str
    usage: Dict[str, int]  # {prompt_tokens, completion_tokens, total_tokens}
    cost: Optional[float]
    provider: str = "openai"
    raw_response: Optional[Any] = None


@dataclass
class StreamChunk:
    """Streaming response chunk.

    Attributes:
        content: Delta text content
        finish_reason: Finish reason (if final chunk)
        raw_chunk: Original provider chunk
    """
    content: str
    finish_reason: Optional[str] = None
    raw_chunk: Optional[Any] = None


@dataclass
class EmbeddingResponse:
    """Unified embedding response format.

    Attributes:
        embeddings: List of embedding vectors (one per input text)
        model: Model used
        usage: Token usage statistics
        cost: Estimated cost (USD)
        provider: Provider name
        raw_response: Original provider response
    """
    embeddings: List[List[float]]
    model: str
    usage: Dict[str, int]  # {prompt_tokens, total_tokens}
    cost: Optional[float]
    provider: str = "openai"
    raw_response: Optional[Any] = None


class OpenAIAdapter:
    """OpenAI Chat API adapter with unified interface.

    Usage:
        # Basic usage
        adapter = OpenAIAdapter(api_key="sk-...")
        response = adapter.chat(
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-4"
        )

        # Streaming
        for chunk in adapter.chat_stream(messages=[...], model="gpt-4"):
            print(chunk.content, end="")
    """

    # Chat pricing per 1K tokens (as of 2025-11-14)
    # Source: https://openai.com/pricing
    PRICING = {
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},
        "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
    }

    # Embeddings pricing per 1M tokens (as of 2025-11-14)
    # Source: https://openai.com/pricing
    EMBEDDING_PRICING = {
        "text-embedding-3-small": 0.02,
        "text-embedding-3-large": 0.13,
        "text-embedding-ada-002": 0.10,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3
    ):
        """Initialize OpenAI adapter.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: Custom API base URL (for proxies/local models)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts (handled by SDK)

        Note: Retry logic is applied via @retry_with_backoff decorator on methods
        """
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url,
            timeout=timeout,
            max_retries=0  # We handle retries ourselves via decorator
        )

    def _estimate_tokens(self, messages: List[Dict[str, str]], model: str) -> int:
        """Estimate token count for messages (pre-request).

        Simple heuristic: ~4 chars per token (rough approximation)

        TODO: Use tiktoken for accurate counting (production implementation)

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

        prompt_cost = (usage["prompt_tokens"] / 1000) * pricing["prompt"]
        completion_cost = (usage["completion_tokens"] / 1000) * pricing["completion"]

        return prompt_cost + completion_cost

    @retry_with_backoff
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        **kwargs
    ) -> ChatResponse:
        """Send chat completion request.

        Args:
            messages: Chat messages [{"role": "user", "content": "..."}]
            model: Model name (e.g., "gpt-4", "gpt-4o", "gpt-3.5-turbo")
            max_tokens: Maximum completion tokens
            temperature: Sampling temperature (0-2)
            **kwargs: Additional parameters passed to OpenAI API

        Returns:
            ChatResponse with unified format

        Raises:
            LLMError: On API errors (mapped to unified hierarchy)
        """
        # Pre-request token estimation
        estimated_tokens = self._estimate_tokens(messages, model)
        print(f"  Estimated prompt tokens: {estimated_tokens}")

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            # Extract response
            content = response.choices[0].message.content

            # Post-request token actuals (from API response)
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

            # Calculate cost
            cost = self._calculate_cost(usage, model)

            return ChatResponse(
                content=content,
                model=response.model,
                usage=usage,
                cost=cost,
                provider="openai",
                raw_response=response
            )

        except Exception as e:
            # Map to unified exception hierarchy
            raise map_openai_exception(e)

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        max_tokens: Optional[int] = None,
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
            StreamChunk for each token/delta

        Raises:
            LLMError: On API errors (mapped to unified hierarchy)

        Note: No @retry_with_backoff on streaming (retries would duplicate content)
        """
        # Pre-request token estimation
        estimated_tokens = self._estimate_tokens(messages, model)
        print(f"  Estimated prompt tokens: {estimated_tokens}")

        try:
            # Call OpenAI streaming API
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                **kwargs
            )

            # Yield chunks as simple iterator (Pythonic pattern from L002)
            for chunk in stream:
                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason

                if delta.content:
                    yield StreamChunk(
                        content=delta.content,
                        finish_reason=finish_reason,
                        raw_chunk=chunk
                    )

                if finish_reason:
                    # Final chunk - include usage if available
                    # Note: OpenAI doesn't provide usage in streaming (limitation)
                    break

        except Exception as e:
            # Map to unified exception hierarchy
            raise map_openai_exception(e)

    def _calculate_embedding_cost(self, usage: Dict[str, int], model: str) -> Optional[float]:
        """Calculate cost for embeddings request.

        Args:
            usage: Token usage dict {prompt_tokens, total_tokens}
            model: Model name

        Returns:
            Cost in USD, or None if pricing unavailable
        """
        # Normalize model name
        base_model = model
        for known_model in self.EMBEDDING_PRICING.keys():
            if known_model in model:
                base_model = known_model
                break

        pricing = self.EMBEDDING_PRICING.get(base_model)
        if not pricing:
            return None

        # Embeddings pricing is per 1M tokens (different from chat pricing per 1K)
        return (usage["prompt_tokens"] / 1_000_000) * pricing

    @retry_with_backoff
    def embed(
        self,
        texts: Union[str, List[str]],
        model: str = "text-embedding-3-small",
        **kwargs
    ) -> EmbeddingResponse:
        """Generate embeddings for text(s).

        Args:
            texts: Single text string or list of text strings
            model: Embedding model name (e.g., "text-embedding-3-small")
            **kwargs: Additional parameters passed to OpenAI API

        Returns:
            EmbeddingResponse with unified format

        Raises:
            LLMError: On API errors (mapped to unified hierarchy)

        Example:
            # Single text
            response = adapter.embed("Hello world")
            embedding = response.embeddings[0]  # List[float]

            # Batch processing
            response = adapter.embed(["Text 1", "Text 2", "Text 3"])
            embeddings = response.embeddings  # List[List[float]]
        """
        # Normalize input to list
        is_single = isinstance(texts, str)
        input_texts = [texts] if is_single else texts

        try:
            # Call OpenAI Embeddings API
            response = self.client.embeddings.create(
                model=model,
                input=input_texts,
                **kwargs
            )

            # Extract embeddings
            embeddings = [item.embedding for item in response.data]

            # Extract usage
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens
            }

            # Calculate cost
            cost = self._calculate_embedding_cost(usage, model)

            return EmbeddingResponse(
                embeddings=embeddings,
                model=response.model,
                usage=usage,
                cost=cost,
                provider="openai",
                raw_response=response
            )

        except Exception as e:
            # Map to unified exception hierarchy
            raise map_openai_exception(e)

    def __repr__(self) -> str:
        """Return string representation of OpenAIAdapter.

        Returns:
            String representation showing provider and timeout configuration.

        Example:
            >>> adapter = OpenAIAdapter(timeout=30.0)
            >>> print(repr(adapter))
            OpenAIAdapter(model=openai, timeout=30.0)
        """
        return f"OpenAIAdapter(model=openai, timeout={self.client.timeout})"
