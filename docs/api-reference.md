# API Reference

Complete reference for the `llm-connectivity` public API.

## Table of Contents

- [LLMClient](#llmclient) - Main client interface
- [Response Objects](#response-objects) - ChatResponse, StreamChunk, EmbeddingResponse
- [Exceptions](#exceptions) - Error handling
- [Retry Strategies](#retry-strategies) - Automatic retry configuration

---

## LLMClient

The main entry point for all LLM operations. Supports multiple providers with a unified interface.

### Initialization

```python
from llm_connectivity import LLMClient

# Approach 1: Model string (recommended)
client = LLMClient(model="provider/model-name")

# Approach 2: Provider object (advanced)
from llm_connectivity.providers.openai_adapter import OpenAIAdapter
adapter = OpenAIAdapter(api_key="...", timeout=120)
client = LLMClient(provider=adapter)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `str` (optional) | Model string in format `"provider/model-name"` |
| `provider` | `Adapter` (optional) | Pre-configured provider adapter instance |
| `**kwargs` | `Any` | Additional arguments passed to provider adapter |

**Supported Providers:**
- `openai/*` - OpenAI models (GPT-4o, GPT-4o-mini, etc.)
- `google/models/*` - Google Gemini models
- `anthropic/*` - Anthropic Claude models

**Raises:** `ValueError` if neither `model` nor `provider` specified

---

### chat()

Send a chat completion request.

```python
response = client.chat(
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=100,
    temperature=0.7
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `messages` | `list[dict]` | *required* | Chat messages in OpenAI format |
| `model` | `str` (optional) | `None` | Override model (if using provider object) |
| `max_tokens` | `int` (optional) | `None` | Maximum completion tokens |
| `temperature` | `float` (optional) | `1.0` | Sampling temperature (0.0-2.0) |

**Message Format:**
```python
[
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "User message"},
    {"role": "assistant", "content": "Previous response"}
]
```

**Returns:** `ChatResponse` - See [Response Objects](#response-objects)

**Raises:** `LLMError` and subclasses - See [Exceptions](#exceptions)

---

### chat_stream()

Stream chat completion response token-by-token.

```python
for chunk in client.chat_stream(
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=100
):
    print(chunk.content, end='', flush=True)
```

#### Parameters

Same as [`chat()`](#chat)

**Returns:** `Iterator[StreamChunk]` - Iterator of stream chunks

**Raises:** `LLMError` and subclasses

---

### embed()

Generate embeddings for text (OpenAI and Google only).

```python
response = client.embed(
    texts="Hello world",  # or list of texts
    model="text-embedding-3-small"  # optional override
)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `texts` | `str` or `list[str]` | Text(s) to embed |
| `model` | `str` (optional) | Override embedding model |

**Returns:** `EmbeddingResponse` - See [Response Objects](#response-objects)

**Raises:** `AttributeError` if provider doesn't support embeddings (Anthropic)

---

## Response Objects

### ChatResponse

Returned by `chat()` method.

```python
@dataclass
class ChatResponse:
    content: str                # Response text
    model: str                  # Model that generated response
    usage: dict[str, int]       # Token usage stats
    cost: Optional[float]       # Estimated cost in USD
    provider: str               # Provider name
    provider_response: Any      # Raw provider response
```

**Usage Dict:**
```python
{
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
}
```

**Example:**
```python
response = client.chat(messages=[...])
print(response.content)        # "Hello! How can I help?"
print(response.usage)          # {"prompt_tokens": 10, ...}
print(response.cost)           # 0.000045
```

---

### StreamChunk

Yielded by `chat_stream()` iterator.

```python
@dataclass
class StreamChunk:
    content: str                    # Token(s) in this chunk
    finish_reason: Optional[str]    # "stop", "length", etc. (final chunk only)
    raw_chunk: Any                  # Raw provider chunk
```

**Example:**
```python
for chunk in client.chat_stream(messages=[...]):
    if chunk.content:
        print(chunk.content, end='')
    if chunk.finish_reason:
        print(f"\nFinished: {chunk.finish_reason}")
```

---

### EmbeddingResponse

Returned by `embed()` method.

```python
@dataclass
class EmbeddingResponse:
    embeddings: list[list[float]]   # List of embedding vectors
    model: str                      # Embedding model used
    usage: dict[str, int]           # Token usage
    cost: Optional[float]           # Estimated cost in USD
    provider: str                   # Provider name
```

**Example:**
```python
response = client.embed("Hello world")
print(len(response.embeddings))          # 1 (single text)
print(len(response.embeddings[0]))       # 1536 (embedding dimensions)
```

---

## Exceptions

All exceptions inherit from `LLMError` base class.

### Exception Hierarchy

```
LLMError (base)
├── AuthenticationError         # Invalid API key
├── RateLimitError             # Quota exceeded (retryable)
├── ContextWindowExceededError # Input too long
├── ValidationError            # Invalid parameters
├── NetworkError               # Connection issues (retryable)
├── ProviderError              # Generic provider error
├── ModelNotFoundError         # Invalid model name
└── InsufficientCreditsError   # No credits remaining
```

### LLMError (Base Class)

```python
class LLMError(Exception):
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        provider_error: Optional[Exception] = None,
        details: Optional[dict] = None
    )
```

**Attributes:**
- `message` (`str`) - Error description
- `provider` (`str`) - Provider name ("openai", "google", "anthropic")
- `provider_error` (`Exception`) - Original provider exception
- `details` (`dict`) - Additional error context

### Retryable Errors

These errors trigger automatic retry with exponential backoff:

#### RateLimitError

```python
try:
    response = client.chat(messages=[...])
except RateLimitError as e:
    # Already retried 3 times automatically
    print(f"Rate limit: {e}")
```

**Retry Behavior:** 3 retries, 2x exponential backoff (1s, 2s, 4s)

#### NetworkError

```python
try:
    response = client.chat(messages=[...])
except NetworkError as e:
    # Already retried 3 times automatically
    print(f"Network error: {e}")
```

**Retry Behavior:** 3 retries, 1.5x exponential backoff (2s, 3s, 4.5s)

### Non-Retryable Errors

These errors require code changes and don't retry:

#### AuthenticationError

Invalid API key - check environment variable.

#### ValidationError / ContextWindowExceededError

Invalid parameters or input too long - reduce `max_tokens` or input size.

#### ModelNotFoundError

Invalid model name - check model string format.

### Catching All LLM Errors

```python
from llm_connectivity.errors import LLMError

try:
    response = client.chat(messages=[...])
except LLMError as e:
    print(f"Provider: {e.provider}")
    print(f"Error: {e}")
    print(f"Original: {e.provider_error}")
```

---

## Retry Strategies

Automatic retry with differentiated exponential backoff.

### Retry Configuration

| Error Type | Max Retries | Backoff Multiplier | Min Delay | Max Delay |
|-----------|-------------|-------------------|-----------|-----------|
| `RateLimitError` | 3 | 2.0 (aggressive) | 1s | 120s |
| `NetworkError` | 3 | 1.5 (moderate) | 2s | 30s |
| `ValidationError` | 3 | 1.0 (linear) | 1s | 10s |
| Non-retryable | 0 | N/A | N/A | N/A |

### Backoff Calculation

**Exponential backoff formula:**
```
delay = min_delay * (multiplier ** (attempt - 1))
delay = min(delay, max_delay)  # Clamp to maximum
```

**Example (RateLimitError):**
- Attempt 1: `1.0 * (2.0 ** 0)` = 1.0s delay
- Attempt 2: `1.0 * (2.0 ** 1)` = 2.0s delay
- Attempt 3: `1.0 * (2.0 ** 2)` = 4.0s delay
- Total: 3 retries over 7 seconds

### Disabling Retry

Retry is built-in and cannot be disabled per-request. To implement custom retry logic, catch the exception and handle it yourself.

---

## Model String Format

All models use the pattern: `{provider}/{model-name}`

### OpenAI Models

```python
"openai/gpt-4o"
"openai/gpt-4o-mini"
"openai/gpt-4-turbo"
"openai/gpt-3.5-turbo"
"openai/text-embedding-3-small"  # Embeddings
"openai/text-embedding-3-large"  # Embeddings
```

### Google Models

```python
"google/models/gemini-2.5-pro"
"google/models/gemini-2.5-flash"
"google/models/gemini-2.0-flash"
```

### Anthropic Models

```python
"anthropic/claude-3-5-sonnet-20241022"
"anthropic/claude-3-opus-20240229"
"anthropic/claude-3-haiku-20240307"
```

---

## Environment Variables

API keys are loaded from environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Google
export GOOGLE_AI_API_KEY="AIza..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

Alternatively, pass API keys explicitly:

```python
from llm_connectivity.providers.openai_adapter import OpenAIAdapter

adapter = OpenAIAdapter(api_key="sk-...")
client = LLMClient(provider=adapter)
```

---

## Complete Examples

See the [`examples/`](examples/) directory for working code samples:

- [`basic_chat.py`](examples/basic_chat.py) - Basic usage
- [`provider_switching.py`](examples/provider_switching.py) - Provider switching
- [`error_handling.py`](examples/error_handling.py) - Exception handling
- [`streaming.py`](examples/streaming.py) - Streaming responses
- [`cost_optimization.py`](examples/cost_optimization.py) - Cost optimization

---

## Additional Resources

- [Tutorial 01: Basic Usage](tutorials/01-basic-usage.md)
- [Tutorial 02: Provider Switching](tutorials/02-provider-switching.md)
- [Tutorial 03: Error Handling](tutorials/03-error-handling.md)
- [Tutorial 04: Streaming](tutorials/04-streaming.md)
- [Tutorial 05: Cost Optimization](tutorials/05-cost-optimization.md)

---

**Version:** v0.1.0-alpha
**Last Updated:** 2025-11-14
