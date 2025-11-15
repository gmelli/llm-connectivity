"""
Example: Basic Chat Completion

This example demonstrates the simplest way to use llm-connectivity for chat completion.

Setup:
    export OPENAI_API_KEY="your-key-here"
    # OR set in code: os.environ["OPENAI_API_KEY"] = "your-key"

Expected output:
    Response: Hello! How can I help you today?
    Model: gpt-4o-mini-2024-07-18
    Tokens used: 27 (prompt: 9, completion: 9)
    Cost: $0.000006 USD
"""

from llm_connectivity import LLMClient

def main():
    # Initialize client with model string (provider/model format)
    client = LLMClient(model="openai/gpt-4o-mini")

    # Send a simple chat message
    response = client.chat(
        messages=[
            {"role": "user", "content": "Say hello and offer to help"}
        ],
        max_tokens=20  # Limit response length
    )

    # Access response data
    print(f"Response: {response.content}")
    print(f"Model: {response.model}")
    print(f"Tokens used: {response.usage['total_tokens']} "
          f"(prompt: {response.usage['prompt_tokens']}, "
          f"completion: {response.usage['completion_tokens']})")
    print(f"Cost: ${response.cost:.6f} USD")

if __name__ == "__main__":
    main()
