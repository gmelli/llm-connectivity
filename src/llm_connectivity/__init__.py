"""LLM Connectivity - Unified interface for multiple LLM providers.

This package provides a consistent, provider-agnostic interface for interacting
with Large Language Model APIs from OpenAI, Anthropic, Google, and more.

Example:
    >>> from llm_connectivity import LLMClient
    >>> client = LLMClient(model="openai/gpt-4o")
    >>> response = client.chat(
    ...     messages=[{"role": "user", "content": "Hello!"}]
    ... )
    >>> print(response.content)
"""

__version__ = "0.0.1"
__author__ = "Gabor Melli"
__license__ = "MIT"

# Public API
from llm_connectivity.client import LLMClient
from llm_connectivity.errors import (
    AuthenticationError,
    ContextWindowExceededError,
    InsufficientCreditsError,
    LLMError,
    ModelNotFoundError,
    NetworkError,
    ProviderError,
    RateLimitError,
    ValidationError,
)
from llm_connectivity.providers.openai_adapter import ChatResponse, EmbeddingResponse, StreamChunk

__all__ = [
    "__version__",
    "LLMClient",
    "ChatResponse",
    "StreamChunk",
    "EmbeddingResponse",
    "LLMError",
    "AuthenticationError",
    "RateLimitError",
    "ContextWindowExceededError",
    "ValidationError",
    "NetworkError",
    "ProviderError",
    "ModelNotFoundError",
    "InsufficientCreditsError",
]
