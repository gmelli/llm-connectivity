# Tutorial: Basic Usage

**Get started with llm-connectivity in 5 minutes**

## What You'll Learn

- How to initialize an LLM client
- How to make your first chat completion request
- How to understand the response structure
- How to track usage and costs

## Prerequisites

- Python 3.9+ installed
- API key for at least one provider:
  ```bash
  export OPENAI_API_KEY="your-key-here"
  # OR
  export GOOGLE_AI_API_KEY="your-key-here"
  # OR
  export ANTHROPIC_API_KEY="your-key-here"
  ```
- Install llm-connectivity:
  ```bash
  pip install llm-connectivity
  ```

## Quick Start (5 Lines of Code)

```python
from llm_connectivity import LLMClient

client = LLMClient(model="openai/gpt-4o-mini")
response = client.chat(messages=[{"role": "user", "content": "Hello!"}])

print(response.content)  # "Hello! How can I help you today?"
```

**That's it!** You've just made your first LLM API call.

## Step-by-Step Guide

### Step 1: Import and Initialize

```python
from llm_connectivity import LLMClient

# Initialize with model string (format: provider/model-name)
client = LLMClient(model="openai/gpt-4o-mini")
```

**Model string format**: `{provider}/{model-name}`
- OpenAI: `"openai/gpt-4o-mini"`
- Google: `"google/models/gemini-2.5-flash"`
- Anthropic: `"anthropic/claude-3-haiku-20240307"`

### Step 2: Make a Chat Request

```python
response = client.chat(
    messages=[
        {"role": "user", "content": "Explain Python in one sentence"}
    ],
    max_tokens=50  # Limit response length
)
```

**Message format**: List of dictionaries with `role` and `content`
- `role`: "user", "assistant", or "system"
- `content`: Your message text

### Step 3: Access the Response

```python
# Get response text
print(response.content)
# Output: "Python is a high-level programming language..."

# Check which model responded
print(response.model)
# Output: "gpt-4o-mini-2024-07-18"

# Check provider
print(response.provider)
# Output: "openai"
```

### Step 4: Monitor Usage and Costs

```python
# Token usage
print(response.usage)
# Output: {
#   "prompt_tokens": 12,
#   "completion_tokens": 18,
#   "total_tokens": 30
# }

# API cost (in USD)
print(f"Cost: ${response.cost:.6f}")
# Output: "Cost: $0.000045"
```

## Complete Example

```python
from llm_connectivity import LLMClient

def ask_llm(question):
    """Ask a question and get detailed response info."""
    # Initialize client
    client = LLMClient(model="openai/gpt-4o-mini")

    # Make request
    response = client.chat(
        messages=[{"role": "user", "content": question}],
        max_tokens=100,
        temperature=0.7  # Creativity level (0.0-2.0)
    )

    # Display results
    print(f"Question: {question}")
    print(f"Answer: {response.content}")
    print(f"Provider: {response.provider}")
    print(f"Tokens: {response.usage['total_tokens']}")
    print(f"Cost: ${response.cost:.6f}")

    return response

# Use it
ask_llm("What is machine learning?")
```

## Configuration Options

### API Key Sources

```python
# Option 1: Environment variable (recommended)
import os
os.environ["OPENAI_API_KEY"] = "your-key"
client = LLMClient(model="openai/gpt-4o-mini")

# Option 2: Direct initialization (provider object)
from llm_connectivity.providers.openai_adapter import OpenAIAdapter

adapter = OpenAIAdapter(api_key="your-key")
client = LLMClient(provider=adapter)
```

### Request Parameters

```python
response = client.chat(
    messages=[...],

    # Optional parameters:
    max_tokens=100,        # Limit response length
    temperature=0.7,       # Creativity (0.0=deterministic, 2.0=creative)
)
```

## Common Response Fields

Every `ChatResponse` includes:

| Field | Type | Description |
|-------|------|-------------|
| `content` | str | The response text |
| `model` | str | Model that generated response |
| `provider` | str | Provider name ("openai", "google", "anthropic") |
| `usage` | dict | Token counts (prompt, completion, total) |
| `cost` | float | Estimated cost in USD |

## Working Example

See [`docs/examples/basic_chat.py`](../examples/basic_chat.py) for a complete, runnable example.

Run it:
```bash
python docs/examples/basic_chat.py
```

## Key Takeaways

✅ **Simple initialization**: `LLMClient(model="provider/model-name")`
✅ **Unified API**: Same `.chat()` method for all providers
✅ **Rich responses**: Content, usage, cost, provider info
✅ **Production-ready**: Built-in error handling and retry logic

## Next Steps

- [Tutorial 02: Provider Switching](02-provider-switching.md) - Switch providers with <1 line change
- [Tutorial 03: Error Handling](03-error-handling.md) - Handle failures gracefully
- [Tutorial 05: Cost Optimization](05-cost-optimization.md) - Minimize API costs

---

**Next**: [Tutorial 02: Provider Switching](02-provider-switching.md)
