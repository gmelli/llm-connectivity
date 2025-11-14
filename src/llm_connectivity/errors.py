"""
Unified Exception Hierarchy for LLM Connectivity

Pattern: litellm-inspired unified exceptions (L002 - 85% confidence)
Purpose: Map provider-specific exceptions to common hierarchy for provider-agnostic error handling

Design Principles:
1. Inherit from common base (LLMError)
2. Preserve provider error details (provider_error attribute)
3. Enable differentiated retry strategies (error type → backoff strategy)
4. Human-readable error messages
"""
from typing import Optional, Dict, Any


class LLMError(Exception):
    """Base exception for all LLM connectivity errors."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        provider_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.provider_error = provider_error
        self.details = details or {}

    def __str__(self):
        parts = [super().__str__()]
        if self.provider:
            parts.append(f"[Provider: {self.provider}]")
        if self.provider_error:
            parts.append(f"[Original: {str(self.provider_error)}]")
        return " ".join(parts)


class AuthenticationError(LLMError):
    """Invalid or missing API credentials."""
    pass


class RateLimitError(LLMError):
    """API rate limit exceeded.

    Retry Strategy: Aggressive exponential backoff (2x multiplier, max 120s)
    """
    pass


class ContextWindowExceededError(LLMError):
    """Request exceeds model's context window.

    Retry Strategy: No retry (requires user intervention to reduce context)
    """
    pass


class ValidationError(LLMError):
    """Request validation failed (invalid parameters, schema mismatch).

    Retry Strategy: Minimal backoff (1x multiplier, max 10s) - for retry-with-context pattern
    """
    pass


class NetworkError(LLMError):
    """Network/connection errors (timeouts, connection refused).

    Retry Strategy: Moderate backoff (1.5x multiplier, max 30s)
    """
    pass


class ProviderError(LLMError):
    """Provider-specific error that doesn't map to common categories."""
    pass


class ModelNotFoundError(LLMError):
    """Requested model not found or not accessible."""
    pass


class InsufficientCreditsError(LLMError):
    """Account has insufficient credits/quota."""
    pass


# Exception mapping helpers
def map_openai_exception(error: Exception) -> LLMError:
    """Map OpenAI SDK exceptions to unified hierarchy.

    Args:
        error: OpenAI exception

    Returns:
        Unified LLMError subclass
    """
    from openai import (
        APIError,
        AuthenticationError as OpenAIAuthError,
        RateLimitError as OpenAIRateLimitError,
        APIConnectionError,
        BadRequestError,
        NotFoundError,
    )

    error_type = type(error).__name__
    error_msg = str(error)

    # Map by exception type
    if isinstance(error, OpenAIAuthError):
        return AuthenticationError(
            f"OpenAI authentication failed: {error_msg}",
            provider="openai",
            provider_error=error
        )

    if isinstance(error, OpenAIRateLimitError):
        return RateLimitError(
            f"OpenAI rate limit exceeded: {error_msg}",
            provider="openai",
            provider_error=error
        )

    if isinstance(error, APIConnectionError):
        return NetworkError(
            f"OpenAI connection error: {error_msg}",
            provider="openai",
            provider_error=error
        )

    if isinstance(error, NotFoundError):
        return ModelNotFoundError(
            f"OpenAI model not found: {error_msg}",
            provider="openai",
            provider_error=error
        )

    if isinstance(error, BadRequestError):
        # Check for context window in message
        if "context" in error_msg.lower() or "token" in error_msg.lower():
            return ContextWindowExceededError(
                f"OpenAI context window exceeded: {error_msg}",
                provider="openai",
                provider_error=error
            )
        return ValidationError(
            f"OpenAI validation error: {error_msg}",
            provider="openai",
            provider_error=error
        )

    # Fallback for unmapped errors
    return ProviderError(
        f"OpenAI error ({error_type}): {error_msg}",
        provider="openai",
        provider_error=error
    )


def map_anthropic_exception(error: Exception) -> LLMError:
    """Map Anthropic SDK exceptions to unified hierarchy.

    Args:
        error: Anthropic exception

    Returns:
        Unified LLMError subclass
    """
    from anthropic import (
        APIError,
        AuthenticationError as AnthropicAuthError,
        RateLimitError as AnthropicRateLimitError,
        APIConnectionError as AnthropicConnectionError,
        BadRequestError as AnthropicBadRequestError,
        NotFoundError as AnthropicNotFoundError,
    )

    error_type = type(error).__name__
    error_msg = str(error)

    # Map by exception type
    if isinstance(error, AnthropicAuthError):
        return AuthenticationError(
            f"Anthropic authentication failed: {error_msg}",
            provider="anthropic",
            provider_error=error
        )

    if isinstance(error, AnthropicRateLimitError):
        return RateLimitError(
            f"Anthropic rate limit exceeded: {error_msg}",
            provider="anthropic",
            provider_error=error
        )

    if isinstance(error, AnthropicConnectionError):
        return NetworkError(
            f"Anthropic connection error: {error_msg}",
            provider="anthropic",
            provider_error=error
        )

    if isinstance(error, AnthropicNotFoundError):
        return ModelNotFoundError(
            f"Anthropic model not found: {error_msg}",
            provider="anthropic",
            provider_error=error
        )

    if isinstance(error, AnthropicBadRequestError):
        # Check for context window in message
        if "context" in error_msg.lower() or "token" in error_msg.lower():
            return ContextWindowExceededError(
                f"Anthropic context window exceeded: {error_msg}",
                provider="anthropic",
                provider_error=error
            )
        return ValidationError(
            f"Anthropic validation error: {error_msg}",
            provider="anthropic",
            provider_error=error
        )

    # Fallback for unmapped errors
    return ProviderError(
        f"Anthropic error ({error_type}): {error_msg}",
        provider="anthropic",
        provider_error=error
    )


def map_google_exception(error: Exception) -> LLMError:
    """Map Google AI SDK exceptions to unified hierarchy.

    Args:
        error: Google AI exception

    Returns:
        Unified LLMError subclass

    Note: Google AI uses different exception types than OpenAI/Anthropic
    """
    error_type = type(error).__name__
    error_msg = str(error)

    # Google AI exceptions (different from OpenAI/Anthropic)
    # Check for common patterns in error messages
    if "401" in error_msg or "authentication" in error_msg.lower() or "api key" in error_msg.lower():
        return AuthenticationError(
            f"Google AI authentication failed: {error_msg}",
            provider="google",
            provider_error=error
        )

    if "429" in error_msg or "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
        return RateLimitError(
            f"Google AI rate limit exceeded: {error_msg}",
            provider="google",
            provider_error=error
        )

    if "404" in error_msg or "not found" in error_msg.lower() or "model" in error_msg.lower():
        return ModelNotFoundError(
            f"Google AI model not found: {error_msg}",
            provider="google",
            provider_error=error
        )

    if "context" in error_msg.lower() or "too long" in error_msg.lower() or "maximum" in error_msg.lower():
        return ContextWindowExceededError(
            f"Google AI context window exceeded: {error_msg}",
            provider="google",
            provider_error=error
        )

    if "400" in error_msg or "invalid" in error_msg.lower() or "bad request" in error_msg.lower():
        return ValidationError(
            f"Google AI validation error: {error_msg}",
            provider="google",
            provider_error=error
        )

    if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
        return NetworkError(
            f"Google AI connection error: {error_msg}",
            provider="google",
            provider_error=error
        )

    # Fallback for unmapped errors
    return ProviderError(
        f"Google AI error ({error_type}): {error_msg}",
        provider="google",
        provider_error=error
    )
