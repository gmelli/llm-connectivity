"""
Unit Tests for Retry Logic

Tests retry logic with differentiated exponential backoff.
Target: 95%+ coverage on retry.py
"""

import pytest
from unittest.mock import Mock, patch
from llm_connectivity.retry import (
    RetryStrategy,
    RETRY_STRATEGIES,
    NON_RETRYABLE_ERRORS,
    get_retry_strategy,
    calculate_backoff,
    retry_with_backoff,
)
from llm_connectivity.errors import (
    RateLimitError,
    ValidationError,
    NetworkError,
    ContextWindowExceededError,
    AuthenticationError,
    ModelNotFoundError,
    ProviderError,
)


class TestRetryStrategy:
    """Test RetryStrategy dataclass."""

    def test_retry_strategy_creation(self):
        """Test creating RetryStrategy with all parameters."""
        strategy = RetryStrategy(
            multiplier=2.0,
            min_delay=1.0,
            max_delay=120.0,
            max_retries=3
        )
        assert strategy.multiplier == 2.0
        assert strategy.min_delay == 1.0
        assert strategy.max_delay == 120.0
        assert strategy.max_retries == 3

    def test_retry_strategy_defaults(self):
        """Test RetryStrategy with default max_retries."""
        strategy = RetryStrategy(
            multiplier=1.5,
            min_delay=2.0,
            max_delay=30.0
        )
        assert strategy.max_retries == 3  # Default value


class TestGetRetryStrategy:
    """Test get_retry_strategy function."""

    def test_rate_limit_error_strategy(self):
        """Test RateLimitError gets aggressive backoff (2x)."""
        error = RateLimitError("Rate limit", provider="openai")
        strategy = get_retry_strategy(error)

        assert strategy is not None
        assert strategy.multiplier == 2.0  # Aggressive exponential
        assert strategy.max_delay == 120.0  # Long max delay
        assert strategy.max_retries == 3

    def test_validation_error_strategy(self):
        """Test ValidationError gets minimal backoff (1x)."""
        error = ValidationError("Invalid param", provider="openai")
        strategy = get_retry_strategy(error)

        assert strategy is not None
        assert strategy.multiplier == 1.0  # Linear (no exponential)
        assert strategy.max_delay == 10.0  # Short max delay
        assert strategy.max_retries == 3

    def test_network_error_strategy(self):
        """Test NetworkError gets moderate backoff (1.5x)."""
        error = NetworkError("Connection failed", provider="openai")
        strategy = get_retry_strategy(error)

        assert strategy is not None
        assert strategy.multiplier == 1.5  # Moderate exponential
        assert strategy.max_delay == 30.0  # Medium max delay
        assert strategy.max_retries == 3

    def test_context_window_error_non_retryable(self):
        """Test ContextWindowExceededError is non-retryable."""
        error = ContextWindowExceededError("Too long", provider="openai")
        strategy = get_retry_strategy(error)

        assert strategy is None  # Non-retryable

    def test_authentication_error_non_retryable(self):
        """Test AuthenticationError is non-retryable."""
        error = AuthenticationError("Invalid key", provider="openai")
        strategy = get_retry_strategy(error)

        assert strategy is None  # Non-retryable

    def test_model_not_found_error_non_retryable(self):
        """Test ModelNotFoundError is non-retryable."""
        error = ModelNotFoundError("Model missing", provider="openai")
        strategy = get_retry_strategy(error)

        assert strategy is None  # Non-retryable

    def test_unknown_error_default_strategy(self):
        """Test unknown error gets default strategy."""
        error = ProviderError("Unknown error", provider="openai")
        strategy = get_retry_strategy(error)

        assert strategy is not None
        assert strategy.multiplier == 1.5  # Default moderate
        assert strategy.min_delay == 1.0
        assert strategy.max_delay == 30.0
        assert strategy.max_retries == 3


class TestCalculateBackoff:
    """Test calculate_backoff function."""

    def test_linear_backoff(self):
        """Test linear backoff (multiplier=1.0)."""
        strategy = RetryStrategy(multiplier=1.0, min_delay=1.0, max_delay=10.0)

        # Linear: delay = min_delay * attempt
        assert calculate_backoff(1, strategy) == 1.0  # 1.0 * 1
        assert calculate_backoff(2, strategy) == 2.0  # 1.0 * 2
        assert calculate_backoff(3, strategy) == 3.0  # 1.0 * 3

    def test_exponential_backoff(self):
        """Test exponential backoff (multiplier=2.0)."""
        strategy = RetryStrategy(multiplier=2.0, min_delay=1.0, max_delay=120.0)

        # Exponential: delay = min_delay * (multiplier ** (attempt - 1))
        assert calculate_backoff(1, strategy) == 1.0   # 1.0 * (2.0 ** 0) = 1.0
        assert calculate_backoff(2, strategy) == 2.0   # 1.0 * (2.0 ** 1) = 2.0
        assert calculate_backoff(3, strategy) == 4.0   # 1.0 * (2.0 ** 2) = 4.0
        assert calculate_backoff(4, strategy) == 8.0   # 1.0 * (2.0 ** 3) = 8.0

    def test_moderate_exponential_backoff(self):
        """Test moderate exponential backoff (multiplier=1.5)."""
        strategy = RetryStrategy(multiplier=1.5, min_delay=2.0, max_delay=30.0)

        # Exponential: delay = min_delay * (multiplier ** (attempt - 1))
        assert calculate_backoff(1, strategy) == 2.0    # 2.0 * (1.5 ** 0) = 2.0
        assert calculate_backoff(2, strategy) == 3.0    # 2.0 * (1.5 ** 1) = 3.0
        assert calculate_backoff(3, strategy) == pytest.approx(4.5, rel=1e-9)  # 2.0 * (1.5 ** 2) = 4.5

    def test_max_delay_clamping(self):
        """Test that delay is clamped to max_delay."""
        strategy = RetryStrategy(multiplier=2.0, min_delay=1.0, max_delay=10.0)

        # High attempt numbers should clamp to max_delay
        assert calculate_backoff(10, strategy) == 10.0  # Would be 512.0, clamped to 10.0
        assert calculate_backoff(20, strategy) == 10.0  # Would be huge, clamped to 10.0

    def test_min_delay_clamping(self):
        """Test that delay is clamped to min_delay."""
        strategy = RetryStrategy(multiplier=1.0, min_delay=5.0, max_delay=30.0)

        # Even attempt=1 should be at least min_delay
        assert calculate_backoff(1, strategy) == 5.0  # min(5.0, 5.0 * 1) = 5.0


class TestRetryWithBackoffDecorator:
    """Test retry_with_backoff decorator."""

    def test_success_on_first_attempt_no_retry(self):
        """Test that successful first attempt doesn't retry."""
        mock_func = Mock(return_value="success")
        decorated = retry_with_backoff(mock_func)

        result = decorated("arg1", kwarg1="value1")

        assert result == "success"
        assert mock_func.call_count == 1  # Called only once

    def test_non_retryable_error_raises_immediately(self):
        """Test that non-retryable errors raise immediately without retry."""
        mock_func = Mock(side_effect=AuthenticationError("Invalid key", provider="openai"))
        decorated = retry_with_backoff(mock_func)

        with pytest.raises(AuthenticationError):
            decorated()

        assert mock_func.call_count == 1  # Called only once, no retries

    @patch('time.sleep')
    def test_retryable_error_with_retries(self, mock_sleep):
        """Test that retryable error triggers retries with backoff."""
        # Fail 2 times, succeed on 3rd attempt
        mock_func = Mock(side_effect=[
            RateLimitError("Rate limit", provider="openai"),
            RateLimitError("Rate limit", provider="openai"),
            "success"
        ])
        decorated = retry_with_backoff(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 3  # Initial + 2 retries

        # Verify sleep was called with correct backoff delays
        assert mock_sleep.call_count == 2  # 2 retries = 2 sleeps
        # RateLimitError strategy: multiplier=2.0, min_delay=1.0
        # Retry 1: 1.0 * (2.0 ** 0) = 1.0
        # Retry 2: 1.0 * (2.0 ** 1) = 2.0
        assert mock_sleep.call_args_list[0][0][0] == 1.0
        assert mock_sleep.call_args_list[1][0][0] == 2.0

    @patch('time.sleep')
    def test_max_retries_exhausted_raises_last_error(self, mock_sleep):
        """Test that exceeding max retries raises the last error."""
        # Fail all attempts (initial + 3 retries = 4 total)
        error = RateLimitError("Rate limit", provider="openai")
        mock_func = Mock(side_effect=error)
        decorated = retry_with_backoff(mock_func)

        with pytest.raises(RateLimitError):
            decorated()

        # Initial attempt + 3 retries = 4 total calls
        assert mock_func.call_count == 4
        # 3 retries = 3 sleeps
        assert mock_sleep.call_count == 3

    @patch('time.sleep')
    def test_differentiated_backoff_rate_limit(self, mock_sleep):
        """Test rate limit error uses aggressive backoff (2x)."""
        mock_func = Mock(side_effect=[
            RateLimitError("Rate limit", provider="openai"),
            "success"
        ])
        decorated = retry_with_backoff(mock_func)

        decorated()

        # RateLimitError: multiplier=2.0, min_delay=1.0
        # Retry 1: 1.0 * (2.0 ** 0) = 1.0
        assert mock_sleep.call_args[0][0] == 1.0

    @patch('time.sleep')
    def test_differentiated_backoff_network(self, mock_sleep):
        """Test network error uses moderate backoff (1.5x)."""
        mock_func = Mock(side_effect=[
            NetworkError("Connection failed", provider="openai"),
            "success"
        ])
        decorated = retry_with_backoff(mock_func)

        decorated()

        # NetworkError: multiplier=1.5, min_delay=2.0
        # Retry 1: 2.0 * (1.5 ** 0) = 2.0
        assert mock_sleep.call_args[0][0] == 2.0

    @patch('time.sleep')
    def test_differentiated_backoff_validation(self, mock_sleep):
        """Test validation error uses minimal backoff (1x linear)."""
        mock_func = Mock(side_effect=[
            ValidationError("Invalid param", provider="openai"),
            ValidationError("Invalid param", provider="openai"),
            "success"
        ])
        decorated = retry_with_backoff(mock_func)

        decorated()

        # ValidationError: multiplier=1.0 (linear), min_delay=1.0
        # Retry 1: 1.0 * 1 = 1.0
        # Retry 2: 1.0 * 2 = 2.0
        assert mock_sleep.call_args_list[0][0][0] == 1.0
        assert mock_sleep.call_args_list[1][0][0] == 2.0

    @patch('time.sleep')
    def test_error_type_changes_adapts_strategy(self, mock_sleep):
        """Test that changing error type adapts to new strategy."""
        # First fails with RateLimitError, then with NetworkError, then succeeds
        mock_func = Mock(side_effect=[
            RateLimitError("Rate limit", provider="openai"),
            NetworkError("Connection failed", provider="openai"),
            "success"
        ])
        decorated = retry_with_backoff(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 3

        # Verify different backoff strategies were used
        # Retry 1 (after RateLimitError): 1.0 * (2.0 ** (1-1)) = 1.0 * (2.0 ** 0) = 1.0
        # Retry 2 (after NetworkError, attempt=2): 2.0 * (1.5 ** (2-1)) = 2.0 * 1.5 = 3.0
        assert mock_sleep.call_args_list[0][0][0] == 1.0
        assert mock_sleep.call_args_list[1][0][0] == 3.0  # Attempt 2 with new strategy

    @patch('time.sleep')
    def test_error_type_changes_to_non_retryable_raises(self, mock_sleep):
        """Test that changing to non-retryable error raises immediately."""
        # First fails with RateLimitError (retryable), then with AuthenticationError (non-retryable)
        mock_func = Mock(side_effect=[
            RateLimitError("Rate limit", provider="openai"),
            AuthenticationError("Invalid key", provider="openai"),
        ])
        decorated = retry_with_backoff(mock_func)

        with pytest.raises(AuthenticationError):
            decorated()

        assert mock_func.call_count == 2  # Initial + 1 retry (then raised)
        assert mock_sleep.call_count == 1  # Only 1 sleep before non-retryable error
