# Tutorial: Error Handling

**Build resilient LLM applications with proper error handling**

## What You'll Learn

- Understand the unified exception hierarchy
- Handle different error types appropriately
- Use automatic retry logic for transient failures
- Implement graceful degradation strategies

## Prerequisites

- Complete [Tutorial 01: Basic Usage](01-basic-usage.md)
- API key configured: `export OPENAI_API_KEY="your-key"`
- `llm-connectivity` installed

## The Exception Hierarchy

All errors inherit from `LLMError` and map to specific failure types:

```
LLMError (base)
├── AuthenticationError      # Invalid API key
├── RateLimitError          # Quota exceeded (retryable)
├── ContextWindowExceededError  # Input too long
├── ValidationError         # Invalid parameters
├── NetworkError           # Connection issues (retryable)
├── ProviderError          # Provider-specific errors
├── ModelNotFoundError     # Invalid model name
└── InsufficientCreditsError  # No credits remaining
```

## Non-Retryable Errors

These errors require code changes - automatic retry won't help:

### 1. AuthenticationError

```python
from llm_connectivity import LLMClient
from llm_connectivity.errors import AuthenticationError

try:
    # Invalid API key
    client = LLMClient(model="openai/gpt-4o-mini")  # Wrong/missing key
    response = client.chat(messages=[{"role": "user", "content": "test"}])
except AuthenticationError as e:
    print(f"Fix your API key: {e}")
    # Action: Set correct API key in environment
```

### 2. ValidationError / ContextWindowExceededError

```python
from llm_connectivity.errors import ValidationError, ContextWindowExceededError

try:
    client = LLMClient(model="openai/gpt-4o-mini")
    response = client.chat(
        messages=[{"role": "user", "content": "test"}],
        max_tokens=200000  # Exceeds model limit!
    )
except (ValidationError, ContextWindowExceededError) as e:
    print(f"Reduce token request: {e}")
    # Action: Lower max_tokens or split input
```

### 3. ModelNotFoundError

```python
from llm_connectivity.errors import ModelNotFoundError

try:
    client = LLMClient(model="openai/gpt-nonexistent")
    response = client.chat(messages=[...])
except ModelNotFoundError as e:
    print(f"Check model name: {e}")
    # Action: Use valid model string
```

## Retryable Errors (Automatic Retry)

These errors retry automatically with exponential backoff:

### 1. RateLimitError (Automatic Retry: 2x Backoff)

```python
from llm_connectivity import LLMClient

# Rate limits handled automatically!
client = LLMClient(model="openai/gpt-4o-mini")

# If rate limited:
# - Attempt 1: Initial request
# - Wait 1s (2^0)
# - Attempt 2: Retry
# - Wait 2s (2^1)
# - Attempt 3: Retry
# - Wait 4s (2^2)
# - Attempt 4: Final retry
response = client.chat(messages=[...])  # Succeeds or raises after 3 retries
```

### 2. NetworkError (Automatic Retry: 1.5x Backoff)

```python
# Network issues retry automatically with moderate backoff
# - Attempt 1: Initial request
# - Wait 2s (2 * 1.5^0)
# - Attempt 2: Retry
# - Wait 3s (2 * 1.5^1)
# - Attempt 3: Retry
response = client.chat(messages=[...])
```

## Handling Errors Explicitly

### Catch Specific Exceptions

```python
from llm_connectivity import LLMClient
from llm_connectivity.errors import (
    AuthenticationError,
    RateLimitError,
    NetworkError,
    ModelNotFoundError,
)

def safe_chat(prompt):
    """Chat with comprehensive error handling."""
    try:
        client = LLMClient(model="openai/gpt-4o-mini")
        return client.chat(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )

    except AuthenticationError:
        print("❌ Invalid API key - check environment variable")
        return None

    except ModelNotFoundError:
        print("❌ Model not found - check model string")
        return None

    except RateLimitError:
        print("❌ Rate limit exceeded even after retries")
        # Already retried 3 times automatically
        return None

    except NetworkError:
        print("❌ Network error persisted after retries")
        return None

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

# Use it
response = safe_chat("Hello")
if response:
    print(response.content)
```

### Catch All LLM Errors

```python
from llm_connectivity.errors import LLMError

try:
    client = LLMClient(model="openai/gpt-4o-mini")
    response = client.chat(messages=[...])
except LLMError as e:
    # Catches ALL llm-connectivity errors
    print(f"LLM error: {e}")
    print(f"Provider: {e.provider}")
    print(f"Original error: {e.provider_error}")
```

## Graceful Degradation

### Strategy 1: Fallback to Cheaper Model

```python
def chat_with_fallback(prompt):
    """Try expensive model, fall back to cheaper if rate limited."""
    models = [
        "openai/gpt-4o",           # Try premium model first
        "openai/gpt-4o-mini",      # Fall back to cheaper
    ]

    for model in models:
        try:
            client = LLMClient(model=model)
            return client.chat(messages=[{"role": "user", "content": prompt}])
        except RateLimitError:
            print(f"{model} rate limited, trying next...")
            continue

    raise RuntimeError("All models rate limited!")
```

### Strategy 2: Fallback to Different Provider

```python
def chat_with_provider_fallback(prompt):
    """Try primary provider, fall back to alternatives."""
    providers = [
        "openai/gpt-4o-mini",
        "google/models/gemini-2.5-flash",
        "anthropic/claude-3-haiku-20240307",
    ]

    for model in providers:
        try:
            client = LLMClient(model=model)
            return client.chat(messages=[{"role": "user", "content": prompt}])
        except (RateLimitError, NetworkError, AuthenticationError):
            print(f"{model} failed, trying next...")
            continue

    raise RuntimeError("All providers failed!")
```

### Strategy 3: Retry with Reduced Tokens

```python
from llm_connectivity.errors import ContextWindowExceededError

def chat_with_auto_truncate(prompt, max_tokens=500):
    """Retry with reduced tokens if context exceeded."""
    client = LLMClient(model="openai/gpt-4o-mini")

    while max_tokens >= 50:
        try:
            return client.chat(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
        except ContextWindowExceededError:
            max_tokens //= 2  # Halve token limit
            print(f"Retrying with max_tokens={max_tokens}")

    raise ValueError("Cannot fit request even with minimal tokens")
```

## Complete Working Example

See [`docs/examples/error_handling.py`](../examples/error_handling.py) for demonstrations of all error types.

Run it:
```bash
python docs/examples/error_handling.py
```

## Retry Configuration

Retry behavior is built-in and differentiated by error type:

| Error Type | Retries | Backoff | Max Delay |
|-----------|---------|---------|-----------|
| `RateLimitError` | 3 | 2x (aggressive) | 120s |
| `NetworkError` | 3 | 1.5x (moderate) | 30s |
| `ValidationError` | 3 | 1x (linear) | 10s |
| Non-retryable | 0 | N/A | N/A |

## Key Takeaways

✅ **Unified hierarchy**: All errors inherit from `LLMError`
✅ **Automatic retry**: Rate limits and network errors retry automatically
✅ **Non-retryable**: Auth, validation, model errors need code fixes
✅ **Graceful degradation**: Implement fallback strategies for resilience

## Next Steps

- [Tutorial 04: Streaming](04-streaming.md) - Real-time token-by-token responses
- [Tutorial 05: Cost Optimization](05-cost-optimization.md) - Minimize API costs

---

**Previous**: [Tutorial 02: Provider Switching](02-provider-switching.md)
**Next**: [Tutorial 04: Streaming](04-streaming.md)
