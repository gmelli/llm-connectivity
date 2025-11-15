# Tutorial: Provider Switching

**⭐ CORE VALUE: Switch LLM providers with <1 line of code**

## What You'll Learn

- How to switch between OpenAI, Google, and Anthropic with just the model string
- Why provider-agnostic code matters for production applications
- How to handle provider-specific differences transparently

## Prerequisites

- Python 3.9+ installed
- API keys for at least 2 providers:
  ```bash
  export OPENAI_API_KEY="your-openai-key"
  export GOOGLE_AI_API_KEY="your-google-key"
  export ANTHROPIC_API_KEY="your-anthropic-key"  # Optional
  ```
- `llm-connectivity` installed: `pip install llm-connectivity`

## The Problem

Traditional LLM integration locks you into a single provider:

```python
# OpenAI-specific code
from openai import OpenAI
client = OpenAI(api_key="...")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[...]
)

# Want to switch to Google? Rewrite everything! ❌
from google.generativeai import GenerativeModel
model = GenerativeModel("gemini-2.5-flash")
response = model.generate_content(...)  # Different API!
```

**Result**: Vendor lock-in, expensive migrations, duplicated code.

## The Solution: <1 Line Switching

With `llm-connectivity`, switching providers requires **only changing the model string**:

```python
from llm_connectivity import LLMClient

# OpenAI version
client = LLMClient(model="openai/gpt-4o-mini")
response = client.chat(messages=[{"role": "user", "content": "Hello!"}])

# Google version (ONLY 1 LINE DIFFERENT!)
client = LLMClient(model="google/models/gemini-2.5-flash")
response = client.chat(messages=[{"role": "user", "content": "Hello!"}])  # SAME CODE ✅
```

**That's it!** Same `.chat()` method, same response format, same code logic.

## Step-by-Step Guide

### Step 1: Write Provider-Agnostic Code

Create a reusable function that works with ANY provider:

```python
from llm_connectivity import LLMClient

def chat_with_llm(model_string, prompt):
    """
    Universal chat function - works with ALL providers!
    Only parameter that changes: model_string
    """
    client = LLMClient(model=model_string)
    response = client.chat(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )
    return response.content
```

### Step 2: Use the Same Code Across Providers

```python
# OpenAI
response = chat_with_llm("openai/gpt-4o-mini", "Explain quantum computing")
print(f"OpenAI: {response}")

# Google (SAME FUNCTION!)
response = chat_with_llm("google/models/gemini-2.5-flash", "Explain quantum computing")
print(f"Google: {response}")

# Anthropic (SAME FUNCTION!)
response = chat_with_llm("anthropic/claude-3-haiku-20240307", "Explain quantum computing")
print(f"Anthropic: {response}")
```

### Step 3: Dynamic Provider Selection

Choose provider at runtime based on config, cost, or availability:

```python
import os

def get_best_model():
    """Select cheapest available provider."""
    if os.getenv("GOOGLE_AI_API_KEY"):
        return "google/models/gemini-2.5-flash"  # Cheapest!
    elif os.getenv("OPENAI_API_KEY"):
        return "openai/gpt-4o-mini"
    elif os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic/claude-3-haiku-20240307"
    else:
        raise ValueError("No API keys configured!")

# Use the cheapest model automatically
model = get_best_model()
client = LLMClient(model=model)
response = client.chat(messages=[...])
```

## Model String Format

All models use the pattern: `{provider}/{model-name}`

### OpenAI Models
```python
"openai/gpt-4o"
"openai/gpt-4o-mini"
"openai/gpt-4-turbo"
"openai/gpt-3.5-turbo"
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

## Response Format (Unified Across Providers)

All providers return the same `ChatResponse` structure:

```python
response = client.chat(messages=[...])

# Access response data (same for ALL providers!)
print(response.content)                    # "Hello! How can I help?"
print(response.model)                      # "gpt-4o-mini-2024-07-18"
print(response.provider)                   # "openai"
print(response.usage)                      # {"prompt_tokens": 10, ...}
print(response.cost)                       # 0.00003 (USD)
```

## Real-World Example: Fallback Strategy

Use primary provider, fall back to alternatives if unavailable:

```python
from llm_connectivity import LLMClient
from llm_connectivity.errors import RateLimitError, NetworkError

def chat_with_fallback(prompt):
    """Try primary provider, fall back to alternatives."""
    providers = [
        "openai/gpt-4o-mini",         # Try OpenAI first
        "google/models/gemini-2.5-flash",   # Fall back to Google
        "anthropic/claude-3-haiku-20240307" # Last resort: Anthropic
    ]

    for model in providers:
        try:
            client = LLMClient(model=model)
            return client.chat(messages=[{"role": "user", "content": prompt}])
        except (RateLimitError, NetworkError) as e:
            print(f"Provider {model} failed: {e}, trying next...")
            continue

    raise RuntimeError("All providers failed!")

# Automatically uses first available provider
response = chat_with_fallback("Hello")
print(f"Responded via: {response.provider}")
```

## Complete Working Example

See [`docs/examples/provider_switching.py`](../examples/provider_switching.py) for a complete, runnable example.

## Key Takeaways

✅ **<1 line switching**: Only model string changes
✅ **Same API**: `.chat()`, `.chat_stream()`, `.embed()` work identically
✅ **Same response format**: Unified `ChatResponse` across all providers
✅ **No rewrites**: Provider-agnostic code from day one
✅ **Dynamic selection**: Choose provider at runtime based on cost, availability, or features

## Next Steps

- [Tutorial 03: Error Handling](03-error-handling.md) - Handle rate limits and failures gracefully
- [Tutorial 04: Streaming](04-streaming.md) - Real-time token-by-token responses
- [Tutorial 05: Cost Optimization](05-cost-optimization.md) - Minimize LLM API costs

---

**Previous**: [Tutorial 01: Basic Usage](01-basic-usage.md)
**Next**: [Tutorial 03: Error Handling](03-error-handling.md)
