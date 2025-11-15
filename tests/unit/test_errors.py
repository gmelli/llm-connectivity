"""
Unit Tests for Exception Hierarchy

Tests unified exception hierarchy and provider exception mapping.
Target: 95%+ coverage on errors.py
"""

from unittest.mock import Mock

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
    map_anthropic_exception,
    map_google_exception,
    map_openai_exception,
)


# Helper function to create mock response objects
def create_mock_response():
    """Create mock response with request attribute for SDK exceptions."""
    mock_request = Mock()
    mock_response = Mock()
    mock_response.request = mock_request
    return mock_response


class TestLLMError:
    """Test base LLMError exception."""

    def test_init_with_message_only(self):
        """Test initialization with message only."""
        error = LLMError("Test error")
        assert str(error) == "Test error"
        assert error.provider is None
        assert error.provider_error is None
        assert error.details == {}

    def test_init_with_provider(self):
        """Test initialization with provider."""
        error = LLMError("Test error", provider="openai")
        assert "Test error" in str(error)
        assert "[Provider: openai]" in str(error)

    def test_init_with_provider_error(self):
        """Test initialization with provider error."""
        original_error = ValueError("Original error")
        error = LLMError("Test error", provider="openai", provider_error=original_error)

        assert "Test error" in str(error)
        assert "[Provider: openai]" in str(error)
        assert "[Original: Original error]" in str(error)
        assert error.provider_error == original_error

    def test_init_with_details(self):
        """Test initialization with details dict."""
        details = {"retry_after": 60, "quota": "daily"}
        error = LLMError("Test error", details=details)
        assert error.details == details


class TestSpecificExceptions:
    """Test specific exception types."""

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid API key", provider="openai")
        assert isinstance(error, LLMError)
        assert "Invalid API key" in str(error)
        assert "[Provider: openai]" in str(error)

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("Rate limit exceeded", provider="anthropic")
        assert isinstance(error, LLMError)
        assert "Rate limit exceeded" in str(error)

    def test_context_window_exceeded_error(self):
        """Test ContextWindowExceededError."""
        error = ContextWindowExceededError("Context too long", provider="openai")
        assert isinstance(error, LLMError)
        assert "Context too long" in str(error)

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid parameter", provider="google")
        assert isinstance(error, LLMError)
        assert "Invalid parameter" in str(error)

    def test_network_error(self):
        """Test NetworkError."""
        error = NetworkError("Connection timeout", provider="openai")
        assert isinstance(error, LLMError)
        assert "Connection timeout" in str(error)

    def test_provider_error(self):
        """Test ProviderError."""
        error = ProviderError("Unknown provider error", provider="openai")
        assert isinstance(error, LLMError)
        assert "Unknown provider error" in str(error)

    def test_model_not_found_error(self):
        """Test ModelNotFoundError."""
        error = ModelNotFoundError("Model not found", provider="anthropic")
        assert isinstance(error, LLMError)
        assert "Model not found" in str(error)

    def test_insufficient_credits_error(self):
        """Test InsufficientCreditsError."""
        error = InsufficientCreditsError("No credits", provider="openai")
        assert isinstance(error, LLMError)
        assert "No credits" in str(error)


class TestMapOpenAIException:
    """Test OpenAI exception mapping."""

    def test_map_authentication_error(self):
        """Test mapping OpenAI AuthenticationError."""
        from openai import AuthenticationError as OpenAIAuthError

        original_error = OpenAIAuthError(
            "Invalid API key", response=create_mock_response(), body=None
        )

        mapped = map_openai_exception(original_error)

        assert isinstance(mapped, AuthenticationError)
        assert "Invalid API key" in str(mapped)
        assert mapped.provider == "openai"
        assert mapped.provider_error == original_error

    def test_map_rate_limit_error(self):
        """Test mapping OpenAI RateLimitError."""
        from openai import RateLimitError as OpenAIRateLimitError

        original_error = OpenAIRateLimitError(
            "Rate limit exceeded", response=create_mock_response(), body=None
        )

        mapped = map_openai_exception(original_error)

        assert isinstance(mapped, RateLimitError)
        assert "rate limit" in str(mapped).lower()
        assert mapped.provider == "openai"

    def test_map_network_error(self):
        """Test mapping OpenAI APIConnectionError."""
        from openai import APIConnectionError

        original_error = APIConnectionError(request=None)

        mapped = map_openai_exception(original_error)

        assert isinstance(mapped, NetworkError)
        assert mapped.provider == "openai"

    def test_map_model_not_found_error(self):
        """Test mapping OpenAI NotFoundError."""
        from openai import NotFoundError

        original_error = NotFoundError(
            "Model not found", response=create_mock_response(), body=None
        )

        mapped = map_openai_exception(original_error)

        assert isinstance(mapped, ModelNotFoundError)
        assert "not found" in str(mapped).lower()

    def test_map_context_window_error(self):
        """Test mapping OpenAI BadRequestError with context window."""
        from openai import BadRequestError

        original_error = BadRequestError(
            "Maximum context length exceeded", response=create_mock_response(), body=None
        )

        mapped = map_openai_exception(original_error)

        assert isinstance(mapped, ContextWindowExceededError)
        assert "context" in str(mapped).lower()

    def test_map_validation_error(self):
        """Test mapping OpenAI BadRequestError without context/token keywords."""
        from openai import BadRequestError

        original_error = BadRequestError(
            "Invalid parameter", response=create_mock_response(), body=None
        )

        mapped = map_openai_exception(original_error)

        assert isinstance(mapped, ValidationError)
        assert "validation" in str(mapped).lower()

    def test_map_unknown_error_to_provider_error(self):
        """Test mapping unknown OpenAI error to ProviderError."""
        original_error = RuntimeError("Unknown error")

        mapped = map_openai_exception(original_error)

        assert isinstance(mapped, ProviderError)
        assert "RuntimeError" in str(mapped)
        assert mapped.provider == "openai"


class TestMapAnthropicException:
    """Test Anthropic exception mapping."""

    def test_map_authentication_error(self):
        """Test mapping Anthropic AuthenticationError."""
        from anthropic import AuthenticationError as AnthropicAuthError

        original_error = AnthropicAuthError(
            "Invalid API key", response=create_mock_response(), body=None
        )

        mapped = map_anthropic_exception(original_error)

        assert isinstance(mapped, AuthenticationError)
        assert "Invalid API key" in str(mapped)
        assert mapped.provider == "anthropic"

    def test_map_rate_limit_error(self):
        """Test mapping Anthropic RateLimitError."""
        from anthropic import RateLimitError as AnthropicRateLimitError

        original_error = AnthropicRateLimitError(
            "Rate limit exceeded", response=create_mock_response(), body=None
        )

        mapped = map_anthropic_exception(original_error)

        assert isinstance(mapped, RateLimitError)
        assert mapped.provider == "anthropic"

    def test_map_network_error(self):
        """Test mapping Anthropic APIConnectionError."""
        from anthropic import APIConnectionError as AnthropicConnectionError

        original_error = AnthropicConnectionError(request=None)

        mapped = map_anthropic_exception(original_error)

        assert isinstance(mapped, NetworkError)
        assert mapped.provider == "anthropic"

    def test_map_model_not_found_error(self):
        """Test mapping Anthropic NotFoundError."""
        from anthropic import NotFoundError as AnthropicNotFoundError

        original_error = AnthropicNotFoundError(
            "Model not found", response=create_mock_response(), body=None
        )

        mapped = map_anthropic_exception(original_error)

        assert isinstance(mapped, ModelNotFoundError)
        assert mapped.provider == "anthropic"

    def test_map_context_window_error(self):
        """Test mapping Anthropic BadRequestError with context keywords."""
        from anthropic import BadRequestError as AnthropicBadRequestError

        original_error = AnthropicBadRequestError(
            "Context length exceeded", response=create_mock_response(), body=None
        )

        mapped = map_anthropic_exception(original_error)

        assert isinstance(mapped, ContextWindowExceededError)
        assert mapped.provider == "anthropic"

    def test_map_validation_error(self):
        """Test mapping Anthropic BadRequestError."""
        from anthropic import BadRequestError as AnthropicBadRequestError

        original_error = AnthropicBadRequestError(
            "Invalid request", response=create_mock_response(), body=None
        )

        mapped = map_anthropic_exception(original_error)

        assert isinstance(mapped, ValidationError)
        assert mapped.provider == "anthropic"

    def test_map_unknown_error_to_provider_error(self):
        """Test mapping unknown Anthropic error."""
        original_error = RuntimeError("Unknown error")

        mapped = map_anthropic_exception(original_error)

        assert isinstance(mapped, ProviderError)
        assert "RuntimeError" in str(mapped)


class TestMapGoogleException:
    """Test Google AI exception mapping."""

    def test_map_authentication_error_with_401(self):
        """Test mapping Google error with 401."""
        original_error = ValueError("401 Unauthorized")

        mapped = map_google_exception(original_error)

        assert isinstance(mapped, AuthenticationError)
        assert mapped.provider == "google"

    def test_map_authentication_error_with_api_key(self):
        """Test mapping Google error with API key mention."""
        original_error = ValueError("Invalid API key provided")

        mapped = map_google_exception(original_error)

        assert isinstance(mapped, AuthenticationError)

    def test_map_rate_limit_error_with_429(self):
        """Test mapping Google error with 429."""
        original_error = ValueError("429 Too Many Requests")

        mapped = map_google_exception(original_error)

        assert isinstance(mapped, RateLimitError)
        assert mapped.provider == "google"

    def test_map_rate_limit_error_with_quota(self):
        """Test mapping Google error with quota mention."""
        original_error = ValueError("Quota exceeded")

        mapped = map_google_exception(original_error)

        assert isinstance(mapped, RateLimitError)

    def test_map_model_not_found_error(self):
        """Test mapping Google error with 404."""
        original_error = ValueError("404 Not Found - model doesn't exist")

        mapped = map_google_exception(original_error)

        assert isinstance(mapped, ModelNotFoundError)
        assert mapped.provider == "google"

    def test_map_context_window_error(self):
        """Test mapping Google error with context window."""
        original_error = ValueError("Context length too long")

        mapped = map_google_exception(original_error)

        assert isinstance(mapped, ContextWindowExceededError)
        assert mapped.provider == "google"

    def test_map_validation_error_with_400(self):
        """Test mapping Google error with 400."""
        original_error = ValueError("400 Bad Request")

        mapped = map_google_exception(original_error)

        assert isinstance(mapped, ValidationError)
        assert mapped.provider == "google"

    def test_map_network_error_with_timeout(self):
        """Test mapping Google error with timeout."""
        original_error = TimeoutError("Connection timeout")

        mapped = map_google_exception(original_error)

        assert isinstance(mapped, NetworkError)
        assert mapped.provider == "google"

    def test_map_unknown_error_to_provider_error(self):
        """Test mapping unknown Google error."""
        original_error = RuntimeError("Unknown error")

        mapped = map_google_exception(original_error)

        assert isinstance(mapped, ProviderError)
        assert "RuntimeError" in str(mapped)
        assert mapped.provider == "google"
