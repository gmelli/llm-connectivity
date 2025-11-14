"""LLM Connectivity - Unified interface for multiple LLM providers.

This package provides a consistent, provider-agnostic interface for interacting
with Large Language Model APIs from OpenAI, Anthropic, Google, and more.

Example:
    >>> from llm_connectivity import LLMClient
    >>> client = LLMClient(provider="openai", api_key="your-key")
    >>> response = client.chat(
    ...     model="gpt-4o",
    ...     messages=[{"role": "user", "content": "Hello!"}]
    ... )
    >>> print(response.content)
"""

__version__ = "0.0.1"
__author__ = "Gabor Melli"
__license__ = "MIT"

# Note: Imports will be added as modules are implemented
# from .client import LLMClient
# from .errors import LLMError, RateLimitError, AuthenticationError

__all__ = [
    "__version__",
    # "LLMClient",  # Coming in v0.1.0-alpha
]
