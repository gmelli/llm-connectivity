"""
Example: Provider Switching

This example demonstrates the CORE VALUE of llm-connectivity:
switching between providers requires only changing the model string.

Setup:
    export OPENAI_API_KEY="your-openai-key"
    export GOOGLE_AI_API_KEY="your-google-key"
    export ANTHROPIC_API_KEY="your-anthropic-key"  # Optional

Expected output:
    ===== OpenAI Response =====
    Content: Hello!...
    Provider: openai
    Cost: $0.000005

    ===== Google Response =====
    Content: Hello!...
    Provider: google
    Cost: $0.000003

    ===== Anthropic Response =====
    Content: Hello!...
    Provider: anthropic
    Cost: $0.000010

    ✅ PROOF: Same code works across all providers!
"""

import os
from llm_connectivity import LLMClient

def chat_with_provider(model_string):
    """
    Reusable function that works with ANY provider.
    IDENTICAL CODE - only model parameter changes!
    """
    client = LLMClient(model=model_string)
    response = client.chat(
        messages=[{"role": "user", "content": "Say hello in one sentence"}],
        max_tokens=20
    )
    return response

def main():
    # OpenAI version
    print("===== OpenAI Response =====")
    response = chat_with_provider("openai/gpt-4o-mini")
    print(f"Content: {response.content}")
    print(f"Provider: {response.provider}")
    print(f"Cost: ${response.cost:.6f}\n")

    # Google version (ONLY MODEL STRING CHANGES!)
    print("===== Google Response =====")
    response = chat_with_provider("google/models/gemini-2.5-flash")
    print(f"Content: {response.content}")
    print(f"Provider: {response.provider}")
    print(f"Cost: ${response.cost:.6f}\n")

    # Anthropic version (ONLY MODEL STRING CHANGES!)
    if os.getenv("ANTHROPIC_API_KEY"):
        print("===== Anthropic Response =====")
        response = chat_with_provider("anthropic/claude-3-haiku-20240307")
        print(f"Content: {response.content}")
        print(f"Provider: {response.provider}")
        print(f"Cost: ${response.cost:.6f}\n")

    print("✅ PROOF: Same code works across all providers!")
    print("Only the model string changed - everything else is identical.")

if __name__ == "__main__":
    main()
