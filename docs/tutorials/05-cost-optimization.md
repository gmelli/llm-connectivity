# Tutorial: Cost Optimization

**Minimize LLM API costs while maintaining quality**

## What You'll Learn

- Choose the most cost-effective models
- Set appropriate token limits
- Monitor and track spending
- Optimize prompts for lower costs

## Prerequisites

- Complete [Tutorial 01: Basic Usage](01-basic-usage.md)
- API keys for multiple providers (for price comparison)
- `llm-connectivity` installed

## Understanding LLM Pricing

LLM APIs charge per token (roughly 4 characters = 1 token):

### Price Comparison (as of 2025)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Relative Cost |
|-------|---------------------|----------------------|---------------|
| GPT-4o | $2.50 | $10.00 | High |
| **GPT-4o-mini** | **$0.15** | **$0.60** | **Low** ⭐ |
| Claude Opus | $15.00 | $75.00 | Very High |
| **Claude Haiku** | **$0.25** | **$1.25** | **Low** ⭐ |
| Gemini Pro | $1.25 | $5.00 | Medium |
| **Gemini Flash** | **$0.075** | **$0.30** | **Lowest** ⭐ |

**Key Insight**: Cheapest models are 15-60x less expensive than premium models!

## Strategy 1: Choose Cost-Effective Models

### Use Case-Appropriate Models

```python
from llm_connectivity import LLMClient

# Simple tasks: Use cheapest models
def simple_task(prompt):
    """Classification, extraction, simple Q&A"""
    client = LLMClient(model="google/models/gemini-2.5-flash")  # Cheapest!
    return client.chat(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50
    )

# Complex tasks: Use capable but not premium
def complex_task(prompt):
    """Reasoning, analysis, creative writing"""
    client = LLMClient(model="openai/gpt-4o-mini")  # Good balance
    return client.chat(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )

# Critical tasks only: Premium models
def critical_task(prompt):
    """Mission-critical, high-stakes decisions"""
    client = LLMClient(model="openai/gpt-4o")  # Use sparingly!
    return client.chat(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
```

### Cost Comparison Example

```python
def compare_costs():
    """See actual cost differences."""
    prompt = "Explain AI in one sentence"
    models = [
        "google/models/gemini-2.5-flash",  # Cheapest
        "openai/gpt-4o-mini",              # Low cost
        "openai/gpt-4o",                   # Premium
    ]

    for model in models:
        client = LLMClient(model=model)
        response = client.chat(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=30
        )
        print(f"{model}: ${response.cost:.6f}")

    # Output:
    # gemini-2.5-flash: $0.000008
    # gpt-4o-mini: $0.000015
    # gpt-4o: $0.000250  (31x more expensive!)
```

## Strategy 2: Limit Token Usage

### Set Appropriate max_tokens

```python
client = LLMClient(model="openai/gpt-4o-mini")

# Bad: No limit (expensive!)
response = client.chat(messages=[...])  # Could use 1000+ tokens
cost_unlimited = response.cost  # $0.000600

# Good: Set reasonable limit
response = client.chat(messages=[...], max_tokens=100)
cost_limited = response.cost  # $0.000060 (10x cheaper!)
```

### Token Limit Guidelines

| Task Type | Recommended max_tokens |
|-----------|----------------------|
| Yes/No questions | 10-20 |
| Single sentence | 30-50 |
| Paragraph | 100-200 |
| Short article | 500-1000 |
| Long content | 1500-2000 |

### Monitor Token Usage

```python
def chat_with_budget(prompt, budget_usd=0.01):
    """Only proceed if within budget."""
    client = LLMClient(model="openai/gpt-4o-mini")

    response = client.chat(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )

    if response.cost > budget_usd:
        print(f"⚠️  Cost ${response.cost:.4f} exceeds budget ${budget_usd}")
    else:
        print(f"✅ Cost ${response.cost:.6f} within budget")

    return response
```

## Strategy 3: Optimize Prompts

### Be Concise

```python
# Bad: Verbose prompt (wastes tokens)
prompt_verbose = """
I would like you to please explain to me, in great detail if possible,
what exactly machine learning is, including all of the various aspects
and components that make up this field of study, and please be as
thorough as you can possibly be in your explanation. Thank you!
"""

# Good: Concise prompt (saves tokens)
prompt_concise = "Explain machine learning in 2 sentences"

# Concise version costs ~70% less on prompt tokens!
```

### Reuse System Messages

```python
# Bad: Repeat context every request
for question in questions:
    client.chat(messages=[
        {"role": "system", "content": "You are a Python expert..."},  # Repeated!
        {"role": "user", "content": question}
    ])

# Good: Maintain conversation context
messages = [{"role": "system", "content": "You are a Python expert..."}]

for question in questions:
    messages.append({"role": "user", "content": question})
    response = client.chat(messages=messages)
    messages.append({"role": "assistant", "content": response.content})
    # System message only counted once!
```

## Strategy 4: Track and Monitor Costs

### Session-Level Tracking

```python
class CostTracker:
    """Track costs across multiple requests."""

    def __init__(self):
        self.total_cost = 0.0
        self.request_count = 0

    def chat(self, model, messages, max_tokens=100):
        client = LLMClient(model=model)
        response = client.chat(messages=messages, max_tokens=max_tokens)

        self.total_cost += response.cost
        self.request_count += 1

        return response

    def report(self):
        print(f"Total requests: {self.request_count}")
        print(f"Total cost: ${self.total_cost:.4f}")
        print(f"Average cost: ${self.total_cost / self.request_count:.6f}")

# Usage
tracker = CostTracker()

tracker.chat("openai/gpt-4o-mini", [{"role": "user", "content": "Hello"}])
tracker.chat("openai/gpt-4o-mini", [{"role": "user", "content": "Goodbye"}])

tracker.report()
# Output:
# Total requests: 2
# Total cost: $0.0003
# Average cost: $0.000150
```

### Daily Budget Enforcement

```python
class BudgetEnforcer:
    """Enforce daily spending limits."""

    def __init__(self, daily_budget_usd=1.00):
        self.daily_budget = daily_budget_usd
        self.daily_spend = 0.0

    def chat(self, model, messages, max_tokens=100):
        client = LLMClient(model=model)
        response = client.chat(messages=messages, max_tokens=max_tokens)

        self.daily_spend += response.cost

        if self.daily_spend > self.daily_budget:
            raise RuntimeError(
                f"Daily budget ${self.daily_budget} exceeded! "
                f"Current spend: ${self.daily_spend:.4f}"
            )

        print(f"Remaining budget: ${self.daily_budget - self.daily_spend:.4f}")
        return response

# Usage
enforcer = BudgetEnforcer(daily_budget_usd=0.50)
response = enforcer.chat("openai/gpt-4o-mini", [{"role": "user", "content": "test"}])
```

## Strategy 5: Dynamic Model Selection

### Choose Cheapest Available Provider

```python
import os

def get_cheapest_model():
    """Select cheapest available provider."""
    if os.getenv("GOOGLE_AI_API_KEY"):
        return "google/models/gemini-2.5-flash"  # Cheapest!
    elif os.getenv("OPENAI_API_KEY"):
        return "openai/gpt-4o-mini"
    elif os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic/claude-3-haiku-20240307"
    else:
        raise ValueError("No API keys configured!")

# Always use cheapest option
client = LLMClient(model=get_cheapest_model())
```

### Tier-Based Selection

```python
def get_model_for_task(complexity="simple"):
    """Select model based on task complexity."""
    tiers = {
        "simple": "google/models/gemini-2.5-flash",  # $0.075/1M
        "medium": "openai/gpt-4o-mini",              # $0.15/1M
        "complex": "anthropic/claude-3-5-sonnet",    # $3.00/1M (only when needed!)
    }
    return tiers.get(complexity, tiers["medium"])

# Use appropriate tier
response = client.chat(model=get_model_for_task("simple"), messages=[...])
```

## Complete Working Example

See [`docs/examples/cost_optimization.py`](../examples/cost_optimization.py) for comprehensive cost optimization demonstrations.

Run it:
```bash
python docs/examples/cost_optimization.py
```

## Cost Optimization Checklist

✅ **Choose wisely**: Use cheapest model that meets quality requirements
✅ **Set limits**: Always specify `max_tokens` appropriate for task
✅ **Be concise**: Shorter prompts = lower costs
✅ **Track spending**: Monitor costs per request and per session
✅ **Enforce budgets**: Prevent runaway costs with spending limits
✅ **Compare providers**: Google Flash often 50%+ cheaper than alternatives

## Quick Wins

1. **Switch to cheaper models**: Often 10-60x cost reduction with minimal quality loss
2. **Set max_tokens=50**: For simple tasks, prevents over-generation
3. **Use Gemini Flash**: Cheapest option for most tasks ($0.075/1M vs $0.15-$15/1M)

## Key Takeaways

✅ **Model choice matters most**: 15-60x cost difference between models
✅ **Token limits are critical**: Set `max_tokens` to prevent over-spending
✅ **Monitor religiously**: Track `response.cost` on every request
✅ **Optimize prompts**: Concise prompts save input token costs
✅ **Google Gemini Flash**: Often the cheapest option (check quality first!)

## Next Steps

- [Tutorial 04: Streaming](04-streaming.md) - Real-time responses
- [API Reference](../api-reference.md) - Complete method documentation

---

**Previous**: [Tutorial 03: Error Handling](03-error-handling.md)
**Next**: [Tutorial 04: Streaming](04-streaming.md)
