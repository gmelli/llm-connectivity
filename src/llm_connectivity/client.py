"""
Unified LLM Client Interface

Pattern: Hybrid provider selection (L002 - 75% confidence)
Purpose: Single interface that works with multiple providers

Key Features:
1. Hybrid provider selection (model string OR provider object)
2. Provider-agnostic interface
3. <5 line provider switching (L002 target)
4. Simple interface (2-3 params covers 80%+ use cases)

Usage Examples:
    # Approach 1: Model string (quick, 80% use case)
    client = LLMClient(model="openai/gpt-4")
    response = client.chat(messages=[{"role": "user", "content": "Hello"}])

    # Approach 2: Provider object (advanced, 20% use case)
    from providers.openai_adapter import OpenAIAdapter
    provider = OpenAIAdapter(api_key="...", timeout=120)
    client = LLMClient(provider=provider)
    response = client.chat(messages=[...])

    # Provider switching (<5 lines)
    # Change line 1: model="openai/gpt-4" → model="anthropic/claude-3-sonnet"
    # Done! (validates L002 target)
"""

from collections.abc import Iterator
from typing import Any, Optional, Union

from llm_connectivity.providers.anthropic_adapter import AnthropicAdapter
from llm_connectivity.providers.google_adapter import GoogleAdapter

# Import adapters
from llm_connectivity.providers.openai_adapter import (
    ChatResponse,
    EmbeddingResponse,
    OpenAIAdapter,
    StreamChunk,
)


class LLMClient:
    """Unified LLM client supporting multiple providers.

    Supports two initialization patterns:
    1. Model string: "provider/model-name" (e.g., "openai/gpt-4")
    2. Provider object: Pre-configured adapter instance

    Attributes:
        provider: Provider adapter instance
        model: Model name
    """

    def __init__(
        self,
        model: Optional[str] = None,
        provider: Optional[Union[OpenAIAdapter, AnthropicAdapter, GoogleAdapter]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize LLM client.

        Args:
            model: Model string in format "provider/model-name"
                   Examples: "openai/gpt-4", "openai/gpt-4o", "openai/gpt-3.5-turbo"
            provider: Pre-configured provider adapter (advanced usage)
            **kwargs: Additional arguments passed to provider adapter

        Raises:
            ValueError: If neither model nor provider specified

        Examples:
            # Simple usage (model string)
            client = LLMClient(model="openai/gpt-4")

            # Advanced usage (provider object)
            adapter = OpenAIAdapter(api_key="...", timeout=120)
            client = LLMClient(provider=adapter)
        """
        if provider:
            # Approach 2: Provider object (advanced)
            self.provider = provider
            self.model = None  # Model specified per-request
        elif model:
            # Approach 1: Model string (simple)
            self.provider = self._create_provider_from_string(model, **kwargs)
            self.model = model
        else:
            raise ValueError("Must specify either 'model' or 'provider'")

    def _create_provider_from_string(
        self, model_string: str, **kwargs: Any
    ) -> Union[OpenAIAdapter, AnthropicAdapter, GoogleAdapter]:
        """Create provider adapter from model string.

        Args:
            model_string: Format "provider/model-name"
            **kwargs: Provider-specific arguments

        Returns:
            Provider adapter instance

        Raises:
            ValueError: If provider not supported or invalid format
        """
        if "/" not in model_string:
            raise ValueError(
                f"Invalid model string format: '{model_string}'. "
                f"Expected format: 'provider/model-name' (e.g., 'openai/gpt-4')"
            )

        provider_name, model_name = model_string.split("/", 1)

        if provider_name == "openai":
            return OpenAIAdapter(**kwargs)
        elif provider_name == "anthropic":
            return AnthropicAdapter(**kwargs)
        elif provider_name == "google":
            return GoogleAdapter(**kwargs)
        else:
            raise ValueError(f"Unsupported provider: '{provider_name}'")

    def _extract_model_name(self, model: Optional[str]) -> str:
        """Extract model name from model string or use default.

        Args:
            model: Model string or None

        Returns:
            Model name (without provider prefix)
        """
        if model and "/" in model:
            return model.split("/", 1)[1]
        return model or "gpt-4o"  # Default model

    def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send chat completion request.

        Unified interface that works across all providers.

        Args:
            messages: Chat messages [{"role": "user", "content": "..."}]
            model: Model name (optional, overrides client model)
            max_tokens: Maximum completion tokens
            temperature: Sampling temperature (0-2)
            **kwargs: Additional provider-specific parameters

        Returns:
            ChatResponse with unified format

        Raises:
            LLMError: On API errors (unified hierarchy)

        Example:
            response = client.chat(
                messages=[{"role": "user", "content": "Hello"}]
            )
            print(response.content)
            print(f"Cost: ${response.cost:.4f}")
        """
        model_name = self._extract_model_name(model or self.model)

        return self.provider.chat(  # type: ignore[no-any-return]
            messages=messages,
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> Iterator[StreamChunk]:
        """Send streaming chat completion request.

        Args:
            messages: Chat messages
            model: Model name (optional, overrides client model)
            max_tokens: Maximum completion tokens
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Yields:
            StreamChunk for each delta

        Raises:
            LLMError: On API errors

        Example:
            for chunk in client.chat_stream(messages=[...]):
                print(chunk.content, end="", flush=True)
        """
        model_name = self._extract_model_name(model or self.model)

        yield from self.provider.chat_stream(  # type: ignore[misc]
            messages=messages,
            model=model_name,
            max_tokens=max_tokens,  # type: ignore[arg-type]
            temperature=temperature,
            **kwargs,
        )

    def embed(
        self, texts: Union[str, list[str]], model: Optional[str] = None, **kwargs: Any
    ) -> EmbeddingResponse:
        """Generate embeddings for text(s).

        Unified interface that works across all providers.

        Args:
            texts: Single text string or list of text strings
            model: Model name (optional, overrides client model)
            **kwargs: Additional provider-specific parameters

        Returns:
            EmbeddingResponse with unified format

        Raises:
            LLMError: On API errors (unified hierarchy)
            AttributeError: If provider doesn't support embeddings

        Example:
            # Single text
            response = client.embed("Hello world")
            embedding = response.embeddings[0]

            # Batch processing
            response = client.embed(["Text 1", "Text 2", "Text 3"])
            embeddings = response.embeddings
        """
        # Check if provider has embed method
        if not hasattr(self.provider, "embed"):
            raise AttributeError(
                f"Provider {self.provider.__class__.__name__} does not support embeddings"
            )

        # Extract model name (use provided model or client's model)
        # For embeddings, we extract just the model name without provider prefix
        if model:
            # Model explicitly provided in method call
            model_name = self._extract_model_name(model)
        elif self.model:
            # Use client's model
            model_name = self._extract_model_name(self.model)
        else:
            # No model specified, let provider use its default
            model_name = None

        # Call provider's embed method
        # If model_name is still None, provider will use its own default
        if model_name:
            return self.provider.embed(texts=texts, model=model_name, **kwargs)  # type: ignore[no-any-return]
        else:
            return self.provider.embed(texts=texts, **kwargs)  # type: ignore[no-any-return]

    def __repr__(self) -> str:
        """Return string representation of LLMClient.

        Returns:
            String representation showing provider and model configuration.

        Example:
            >>> client = LLMClient(model="openai/gpt-4o")
            >>> print(repr(client))
            LLMClient(provider=<OpenAIAdapter>, model=openai/gpt-4o)
        """
        return f"LLMClient(provider={self.provider}, model={self.model})"
