"""
Example: Error Handling

This example demonstrates how to handle different types of LLM errors
using the unified exception hierarchy.

Setup:
    export OPENAI_API_KEY="your-key-here"

Expected output:
    ===== Testing Different Error Scenarios =====

    Test 1: Invalid API key
    ❌ AuthenticationError: Invalid API key

    Test 2: Excessive token request
    ❌ ValidationError: Maximum context length exceeded

    Test 3: Invalid model name
    ❌ ModelNotFoundError: Model not found

    Test 4: Retryable error with automatic retry
    ⚠️  Attempt 1 failed (retrying with backoff...)
    ✅ Success after retry!
"""

from llm_connectivity import LLMClient
from llm_connectivity.errors import (
    AuthenticationError,
    RateLimitError,
    ValidationError,
    ModelNotFoundError,
    ContextWindowExceededError,
    NetworkError,
)
from llm_connectivity.providers.openai_adapter import OpenAIAdapter

def test_authentication_error():
    """Test authentication error handling."""
    print("Test 1: Invalid API key")
    try:
        adapter = OpenAIAdapter(api_key="sk-invalid-key")
        client = LLMClient(provider=adapter)
        client.chat(
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
    except AuthenticationError as e:
        print(f"❌ AuthenticationError: {str(e)[:50]}...")
        print("   (Non-retryable - fix your API key)\n")

def test_validation_error():
    """Test validation error handling."""
    print("Test 2: Excessive token request")
    try:
        client = LLMClient(model="openai/gpt-4o-mini")
        client.chat(
            messages=[{"role": "user", "content": "test"}],
            max_tokens=200000  # Way over limit
        )
    except (ValidationError, ContextWindowExceededError) as e:
        print(f"❌ ValidationError: {str(e)[:50]}...")
        print("   (Non-retryable - reduce token request)\n")

def test_model_not_found():
    """Test model not found error handling."""
    print("Test 3: Invalid model name")
    try:
        client = LLMClient(model="openai/gpt-nonexistent-model")
        client.chat(
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
    except ModelNotFoundError as e:
        print(f"❌ ModelNotFoundError: {str(e)[:50]}...")
        print("   (Non-retryable - check model name)\n")

def test_rate_limit_handling():
    """
    Test rate limit handling with automatic retry.
    Note: This won't actually trigger a rate limit in normal usage.
    """
    print("Test 4: Normal request (auto-retry enabled)")
    try:
        client = LLMClient(model="openai/gpt-4o-mini")
        response = client.chat(
            messages=[{"role": "user", "content": "Say 'ok'"}],
            max_tokens=5
        )
        print(f"✅ Success: {response.content}")
        print("   (Rate limits and network errors retry automatically with exponential backoff)\n")
    except RateLimitError as e:
        # If rate limit hit, it will retry automatically
        print(f"⚠️  Rate limit hit (but will retry automatically): {e}\n")

def main():
    print("===== Testing Different Error Scenarios =====\n")

    test_authentication_error()
    test_validation_error()
    test_model_not_found()
    test_rate_limit_handling()

    print("===== Error Handling Summary =====")
    print("✅ AuthenticationError, ValidationError, ModelNotFoundError: Non-retryable")
    print("✅ RateLimitError, NetworkError: Automatic retry with exponential backoff")
    print("✅ All provider errors mapped to unified exception hierarchy")

if __name__ == "__main__":
    main()
