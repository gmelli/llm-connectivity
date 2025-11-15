# Tutorial: Streaming

**Get real-time token-by-token responses for better UX**

## What You'll Learn

- When and why to use streaming
- How to implement basic streaming
- How to track progress and aggregate chunks
- How to handle errors in streams

## Prerequisites

- Complete [Tutorial 01: Basic Usage](01-basic-usage.md)
- API key configured: `export OPENAI_API_KEY="your-key"`
- `llm-connectivity` installed

## Why Use Streaming?

**Without streaming** (traditional):
```python
client = LLMClient(model="openai/gpt-4o-mini")
response = client.chat(messages=[...], max_tokens=500)
print(response.content)  # Waits 5-10s, then prints all at once
```

**With streaming** (real-time):
```python
for chunk in client.chat_stream(messages=[...], max_tokens=500):
    print(chunk.content, end='', flush=True)  # Prints as tokens arrive!
```

**Benefits**:
- ✅ Better UX (user sees progress immediately)
- ✅ Lower perceived latency (output starts in <1s)
- ✅ Early cancellation possible (stop if not relevant)
- ✅ Progress indicators (show dots while generating)

## Basic Streaming

### Simple Example

```python
from llm_connectivity import LLMClient

client = LLMClient(model="openai/gpt-4o-mini")

# Stream tokens as they arrive
for chunk in client.chat_stream(
    messages=[{"role": "user", "content": "Count to 5 with words"}],
    max_tokens=50
):
    if chunk.content:
        print(chunk.content, end='', flush=True)

print()  # Final newline

# Output (arrives progressively):
# One, two, three, four, five.
```

### Understanding Chunks

Each chunk is a `StreamChunk` object:

```python
for chunk in client.chat_stream(messages=[...]):
    print(f"Content: '{chunk.content}'")
    print(f"Finish reason: {chunk.finish_reason}")
    print(f"Raw chunk: {chunk.raw_chunk}")
    print("---")

# Output:
# Content: 'Hello'
# Finish reason: None
# Raw chunk: ChatCompletionChunk(...)
# ---
# Content: ' there'
# Finish reason: None
# ...
# ---
# Content: '!'
# Finish reason: 'stop'  # Final chunk
# ...
```

## Aggregating Chunks

### Build Full Response

```python
def stream_and_aggregate(prompt):
    """Stream tokens and build full response."""
    client = LLMClient(model="openai/gpt-4o-mini")

    chunks = []
    full_response = []

    for chunk in client.chat_stream(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    ):
        chunks.append(chunk)

        if chunk.content:
            full_response.append(chunk.content)
            print(chunk.content, end='', flush=True)

    print()  # Newline after streaming

    # Full aggregated response
    complete_text = ''.join(full_response)

    print(f"\nTotal chunks: {len(chunks)}")
    print(f"Complete response: {complete_text}")

    return complete_text

stream_and_aggregate("Explain Python in one sentence")
```

## Progress Tracking

### Show Progress Dots

```python
def stream_with_progress(prompt):
    """Stream with visual progress indicator."""
    client = LLMClient(model="openai/gpt-4o-mini")

    print("Generating response", end='', flush=True)

    response_parts = []
    for chunk in client.chat_stream(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    ):
        if chunk.content:
            response_parts.append(chunk.content)
            print(".", end='', flush=True)  # Progress dot per chunk

    print()  # Newline
    full_response = ''.join(response_parts)
    print(f"Response: {full_response}")

# Output:
# Generating response..........
# Response: Python is a high-level programming language...
```

### Count Tokens in Real-Time

```python
def stream_with_token_count(prompt):
    """Track approximate tokens as streaming."""
    client = LLMClient(model="openai/gpt-4o-mini")

    token_count = 0
    response_parts = []

    for chunk in client.chat_stream(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    ):
        if chunk.content:
            response_parts.append(chunk.content)
            # Rough estimate: 1 chunk ≈ 1-2 tokens
            token_count += len(chunk.content.split())

            print(f"\rTokens so far: ~{token_count}", end='', flush=True)

    print()  # Newline
    print(f"Final response: {''.join(response_parts)}")

stream_with_token_count("List 3 programming languages")
```

## Error Handling in Streams

### Catch Errors Early

```python
from llm_connectivity.errors import RateLimitError, NetworkError

def safe_stream(prompt):
    """Stream with error handling."""
    client = LLMClient(model="openai/gpt-4o-mini")

    try:
        response_parts = []

        for chunk in client.chat_stream(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        ):
            if chunk.content:
                response_parts.append(chunk.content)
                print(chunk.content, end='', flush=True)

        print()  # Newline
        return ''.join(response_parts)

    except RateLimitError:
        print("\n❌ Rate limit exceeded")
        return None

    except NetworkError:
        print("\n❌ Network error during streaming")
        return None

response = safe_stream("Hello")
if response:
    print(f"Success: {len(response)} characters received")
```

## Streaming vs Non-Streaming

### When to Use Each

**Use Streaming** when:
- User-facing applications (better UX)
- Long responses (>100 tokens)
- Progress feedback needed
- Early cancellation desired

**Use Non-Streaming** when:
- Batch processing (no user watching)
- Short responses (<50 tokens)
- Need full response for processing
- Simplicity preferred

### Performance Comparison

```python
import time

def compare_latency(prompt):
    """Compare perceived latency."""
    client = LLMClient(model="openai/gpt-4o-mini")

    # Non-streaming (traditional)
    print("Non-streaming:")
    start = time.time()
    response = client.chat(messages=[{"role": "user", "content": prompt}], max_tokens=100)
    end = time.time()
    print(f"  Time to first output: {end - start:.2f}s")
    print(f"  Response: {response.content}")

    # Streaming (real-time)
    print("\nStreaming:")
    start = time.time()
    first_chunk_time = None

    for i, chunk in enumerate(client.chat_stream(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )):
        if chunk.content and first_chunk_time is None:
            first_chunk_time = time.time() - start
            print(f"  Time to first output: {first_chunk_time:.2f}s")

    # Streaming typically shows first output 3-5x faster!
```

## Advanced: Streaming with Callbacks

### Real-Time Processing

```python
def stream_with_callback(prompt, on_token):
    """Stream with callback function for each token."""
    client = LLMClient(model="openai/gpt-4o-mini")

    for chunk in client.chat_stream(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    ):
        if chunk.content:
            on_token(chunk.content)  # Custom processing

# Example: Log each token
def log_token(token):
    print(f"[LOG] Received: '{token}'")

stream_with_callback("Say hello", on_token=log_token)
```

## Complete Working Example

See [`docs/examples/streaming.py`](../examples/streaming.py) for comprehensive streaming demonstrations.

Run it:
```bash
python docs/examples/streaming.py
```

## Key Takeaways

✅ **Better UX**: Streaming provides immediate feedback (first token in <1s)
✅ **Simple API**: `client.chat_stream()` returns iterator of `StreamChunk` objects
✅ **Aggregate easily**: Collect chunks into full response with `''.join()`
✅ **Progress tracking**: Show dots, token counts, or custom indicators
✅ **Works everywhere**: Same streaming API across OpenAI, Google, Anthropic

## Common Patterns

```python
# Pattern 1: Print as arrives
for chunk in client.chat_stream(messages=[...]):
    if chunk.content:
        print(chunk.content, end='', flush=True)

# Pattern 2: Aggregate for processing
chunks = list(client.chat_stream(messages=[...]))
full_text = ''.join(chunk.content for chunk in chunks if chunk.content)

# Pattern 3: Progress with aggregation
parts = []
for chunk in client.chat_stream(messages=[...]):
    if chunk.content:
        parts.append(chunk.content)
        print(".", end='', flush=True)
full_response = ''.join(parts)
```

## Next Steps

- [Tutorial 05: Cost Optimization](05-cost-optimization.md) - Minimize API costs
- [API Reference](../api-reference.md) - Complete documentation

---

**Previous**: [Tutorial 03: Error Handling](03-error-handling.md)
**Next**: [Tutorial 05: Cost Optimization](05-cost-optimization.md)
