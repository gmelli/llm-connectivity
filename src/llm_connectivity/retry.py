"""
Retry Logic with Differentiated Exponential Backoff

Pattern: instructor-inspired differentiated retry (L002 - 70% confidence)
Purpose: Intelligent retry with error-type-specific backoff strategies

Key Innovation (from instructor):
- Different backoff strategies by error type
- Rate limits get aggressive backoff (2x multiplier, up to 120s)
- Validation errors get minimal backoff (for retry-with-context pattern)
- Network errors get moderate backoff

Design:
1. RetryStrategy dataclass defines backoff parameters
2. get_retry_strategy() maps error type → strategy
3. retry_with_backoff() decorator applies retry logic
"""

import functools
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

from llm_connectivity.errors import (
    AuthenticationError,
    ContextWindowExceededError,
    ModelNotFoundError,
    NetworkError,
    RateLimitError,
    ValidationError,
)


@dataclass
class RetryStrategy:
    """Retry backoff strategy parameters.

    Attributes:
        multiplier: Exponential backoff multiplier (1.0 = linear, 2.0 = exponential)
        min_delay: Minimum delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        max_retries: Maximum number of retry attempts
    """

    multiplier: float
    min_delay: float
    max_delay: float
    max_retries: int = 3


# Differentiated strategies by error type (from L002 research)
RETRY_STRATEGIES = {
    RateLimitError: RetryStrategy(
        multiplier=2.0,  # Aggressive exponential backoff
        min_delay=1.0,
        max_delay=120.0,
        max_retries=3,
    ),
    ValidationError: RetryStrategy(
        multiplier=1.0,  # Minimal backoff (for retry-with-context)
        min_delay=1.0,
        max_delay=10.0,
        max_retries=3,
    ),
    NetworkError: RetryStrategy(
        multiplier=1.5, min_delay=2.0, max_delay=30.0, max_retries=3  # Moderate backoff
    ),
}

# Non-retryable errors
NON_RETRYABLE_ERRORS = (
    ContextWindowExceededError,  # Requires user intervention
    AuthenticationError,  # Wrong credentials won't fix themselves
    ModelNotFoundError,  # Model doesn't exist or no access
)


def get_retry_strategy(error: Exception) -> Optional[RetryStrategy]:
    """Get retry strategy for an error type.

    Args:
        error: Exception instance

    Returns:
        RetryStrategy if error is retryable, None otherwise
    """
    # Check non-retryable first
    if isinstance(error, NON_RETRYABLE_ERRORS):
        return None

    # Find matching strategy
    for error_type, strategy in RETRY_STRATEGIES.items():
        if isinstance(error, error_type):
            return strategy

    # Default strategy for unknown retryable errors
    return RetryStrategy(multiplier=1.5, min_delay=1.0, max_delay=30.0, max_retries=3)


def calculate_backoff(attempt: int, strategy: RetryStrategy) -> float:
    """Calculate backoff delay for retry attempt.

    Args:
        attempt: Retry attempt number (1-indexed)
        strategy: Retry strategy

    Returns:
        Delay in seconds (clamped to min_delay/max_delay)
    """
    if strategy.multiplier == 1.0:
        # Linear backoff
        delay = strategy.min_delay * attempt
    else:
        # Exponential backoff
        delay = strategy.min_delay * (strategy.multiplier ** (attempt - 1))

    # Clamp to [min_delay, max_delay]
    return max(strategy.min_delay, min(delay, strategy.max_delay))


def retry_with_backoff(func: Callable) -> Callable:
    """Decorator to add retry logic with differentiated backoff.

    Applies error-type-specific retry strategies:
    - Rate limits: Aggressive backoff (2x, up to 120s)
    - Validation: Minimal backoff (1x, up to 10s)
    - Network: Moderate backoff (1.5x, up to 30s)
    - Non-retryable: No retry (auth, context window)

    Usage:
        @retry_with_backoff
        def call_api():
            return api.chat(...)

    Args:
        func: Function to wrap with retry logic

    Returns:
        Wrapped function with retry logic
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        last_error = None

        # Try once without retry
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e

            # Check if retryable
            strategy = get_retry_strategy(e)
            if strategy is None:
                # Non-retryable error
                raise

            # Retry loop
            for attempt in range(1, strategy.max_retries + 1):
                # Calculate backoff
                delay = calculate_backoff(attempt, strategy)

                # Log retry attempt (in production, use proper logging)
                print(
                    f"  Retry {attempt}/{strategy.max_retries} after {delay:.1f}s ({type(last_error).__name__})"
                )

                # Wait
                time.sleep(delay)

                # Retry
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    # Check if error type changed (might not be retryable anymore)
                    new_strategy = get_retry_strategy(e)
                    if new_strategy is None:
                        raise

                    # Continue with new strategy if different
                    if new_strategy != strategy:
                        strategy = new_strategy

            # All retries exhausted
            raise last_error from None

    return wrapper


# Retry-with-context pattern (instructor innovation - L002)
# TODO: Implement in future iteration
# This pattern feeds validation errors back to LLM for self-correction
# Example: Pydantic validation fails → Include error in next prompt → LLM fixes
def retry_with_context(func: Callable, context_builder: Optional[Callable] = None) -> Callable:
    """Retry with error context feedback (future enhancement).

    Pattern from instructor: Feed validation errors to LLM for self-correction.

    Args:
        func: Function to wrap
        context_builder: Function to build context from error

    Returns:
        Wrapped function

    Note: Placeholder for future implementation
    """
    # TODO: Implement retry-with-context pattern
    # This is an advanced pattern from instructor that feeds validation
    # errors back to the LLM to let it self-correct
    return retry_with_backoff(func)
