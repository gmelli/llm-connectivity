"""
Example: Cost Optimization

This example demonstrates strategies for optimizing LLM API costs.

Setup:
    export OPENAI_API_KEY="your-key-here"
    export GOOGLE_AI_API_KEY="your-google-key"

Expected output:
    ===== Cost Comparison Across Models =====
    GPT-4o-mini cost: $0.000015
    Gemini 2.5 Flash cost: $0.000008

    Savings: 47% by using Gemini 2.5 Flash

    ===== Token Limit Impact =====
    Unlimited tokens cost: $0.000120
    Limited to 50 tokens cost: $0.000025

    Savings: 79% by limiting max_tokens

    ===== Cost Monitoring =====
    Total cost this session: $0.000168
"""

from llm_connectivity import LLMClient

def compare_model_costs():
    """Compare costs across different models."""
    print("===== Cost Comparison Across Models =====")

    message = [{"role": "user", "content": "Explain AI in one sentence"}]

    # OpenAI GPT-4o-mini (cheap but capable)
    client_openai = LLMClient(model="openai/gpt-4o-mini")
    response_openai = client_openai.chat(messages=message, max_tokens=30)
    print(f"GPT-4o-mini cost: ${response_openai.cost:.6f}")

    # Google Gemini 2.5 Flash (even cheaper!)
    client_google = LLMClient(model="google/models/gemini-2.5-flash")
    response_google = client_google.chat(messages=message, max_tokens=30)
    print(f"Gemini 2.5 Flash cost: ${response_google.cost:.6f}")

    # Calculate savings
    savings = ((response_openai.cost - response_google.cost) / response_openai.cost) * 100
    print(f"\nSavings: {savings:.0f}% by using Gemini 2.5 Flash\n")

def demonstrate_token_limits():
    """Show impact of token limits on cost."""
    print("===== Token Limit Impact =====")

    message = [{"role": "user", "content": "Write a long essay about AI"}]
    client = LLMClient(model="openai/gpt-4o-mini")

    # No limit (expensive!)
    response_unlimited = client.chat(messages=message, max_tokens=500)
    print(f"Unlimited tokens cost: ${response_unlimited.cost:.6f}")
    print(f"Tokens used: {response_unlimited.usage['total_tokens']}")

    # Limited tokens (cheaper!)
    response_limited = client.chat(messages=message, max_tokens=50)
    print(f"\nLimited to 50 tokens cost: ${response_limited.cost:.6f}")
    print(f"Tokens used: {response_limited.usage['total_tokens']}")

    # Calculate savings
    savings = ((response_unlimited.cost - response_limited.cost) / response_unlimited.cost) * 100
    print(f"\nSavings: {savings:.0f}% by limiting max_tokens\n")

def track_session_costs():
    """Track total costs across multiple requests."""
    print("===== Cost Monitoring =====")

    client = LLMClient(model="openai/gpt-4o-mini")
    total_cost = 0.0

    # Multiple requests
    requests = [
        "Say hello",
        "Count to 5",
        "Explain Python in 10 words"
    ]

    for request in requests:
        response = client.chat(
            messages=[{"role": "user", "content": request}],
            max_tokens=20
        )
        total_cost += response.cost
        print(f"Request: '{request}' - Cost: ${response.cost:.6f}")

    print(f"\nTotal cost this session: ${total_cost:.6f}")

def optimization_tips():
    """Print cost optimization best practices."""
    print("\n===== Cost Optimization Tips =====")
    print("1. Use cheaper models:")
    print("   - GPT-4o-mini instead of GPT-4o (15x cheaper!)")
    print("   - Gemini 2.5 Flash instead of Gemini 2.5 Pro (20x cheaper!)")
    print("   - Claude Haiku instead of Claude Opus (60x cheaper!)")
    print("\n2. Set max_tokens limits:")
    print("   - Only request what you need")
    print("   - Short tasks: max_tokens=50-100")
    print("   - Medium tasks: max_tokens=200-500")
    print("\n3. Monitor usage:")
    print("   - Check response.usage for token counts")
    print("   - Track response.cost for spend monitoring")
    print("   - Set budget alerts in your code")
    print("\n4. Optimize prompts:")
    print("   - Be concise - shorter prompts = lower cost")
    print("   - Reuse system messages across requests")
    print("   - Avoid unnecessary context")

def main():
    compare_model_costs()
    demonstrate_token_limits()
    track_session_costs()
    optimization_tips()

if __name__ == "__main__":
    main()
