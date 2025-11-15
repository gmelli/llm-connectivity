"""
Example: Streaming Chat Completion

This example demonstrates how to use streaming for real-time responses.

Setup:
    export OPENAI_API_KEY="your-key-here"

Expected output:
    ===== Streaming Response =====
    Hello! How can I assist you today?

    ===== Chunked Output =====
    Chunk 1: 'Hello'
    Chunk 2: '!'
    Chunk 3: ' How'
    ...

    Total chunks: 12
    Full response: Hello! How can I assist you today?
"""

from llm_connectivity import LLMClient

def basic_streaming():
    """Simple streaming example - print as tokens arrive."""
    print("===== Streaming Response =====")

    client = LLMClient(model="openai/gpt-4o-mini")

    # Stream chat completion
    for chunk in client.chat_stream(
        messages=[{"role": "user", "content": "Say hello and offer to help in one sentence"}],
        max_tokens=30
    ):
        # Print each chunk as it arrives (no newline)
        if chunk.content:
            print(chunk.content, end='', flush=True)

    print("\n")  # Final newline

def detailed_streaming():
    """Detailed streaming example - show chunk details and aggregation."""
    print("===== Chunked Output =====")

    client = LLMClient(model="openai/gpt-4o-mini")

    chunks = []
    full_response = []

    for i, chunk in enumerate(client.chat_stream(
        messages=[{"role": "user", "content": "Count to 5 with words"}],
        max_tokens=50
    ), 1):
        chunks.append(chunk)

        # Show chunk details
        if chunk.content:
            print(f"Chunk {i}: '{chunk.content}'")
            full_response.append(chunk.content)

        # Check for finish reason
        if chunk.finish_reason:
            print(f"Stream finished: {chunk.finish_reason}")

    print(f"\nTotal chunks: {len(chunks)}")
    print(f"Full response: {''.join(full_response)}")

def streaming_with_progress():
    """Streaming with progress indicator."""
    print("\n===== Streaming with Progress =====")

    client = LLMClient(model="openai/gpt-4o-mini")

    print("Generating response", end='', flush=True)

    response_parts = []
    for chunk in client.chat_stream(
        messages=[{"role": "user", "content": "Explain streaming in one sentence"}],
        max_tokens=40
    ):
        if chunk.content:
            response_parts.append(chunk.content)
            print(".", end='', flush=True)  # Progress indicator

    print("\n")
    print(f"Response: {''.join(response_parts)}")

def main():
    basic_streaming()
    detailed_streaming()
    streaming_with_progress()

    print("\n===== Streaming Summary =====")
    print("✅ Real-time token-by-token output")
    print("✅ Progress tracking with chunk details")
    print("✅ Aggregate chunks to build full response")
    print("✅ Works identically across all providers")

if __name__ == "__main__":
    main()
