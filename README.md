# LLM Connectivity

[![Tests](https://github.com/gmelli/llm-connectivity/actions/workflows/test.yml/badge.svg)](https://github.com/gmelli/llm-connectivity/actions/workflows/test.yml)
[![Lint](https://github.com/gmelli/llm-connectivity/actions/workflows/lint.yml/badge.svg)](https://github.com/gmelli/llm-connectivity/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/gmelli/llm-connectivity/branch/main/graph/badge.svg)](https://codecov.io/gh/gmelli/llm-connectivity)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

A unified Python interface for multiple Large Language Model providers.

## Overview

`llm-connectivity` provides a consistent, provider-agnostic interface for interacting with LLM APIs from OpenAI, Anthropic, Google, and more. Switch providers with a single line of code while maintaining full feature compatibility.

## Features

- **Unified Interface**: Single API for chat completions, streaming, and embeddings across all providers
- **Provider Agnostic**: Switch between OpenAI, Anthropic, Google with **<1 line of code** (just change model string!)
- **Intelligent Retry**: Differentiated exponential backoff strategies for rate limits, network issues, and validation errors
- **Token Management**: Pre-call estimation and post-call actual token tracking with usage monitoring
- **Cost Tracking**: Built-in pricing data for all supported models with automatic cost calculation
- **Exception Handling**: Unified exception hierarchy mapping all provider errors to common types
- **Type Safe**: Full type hints for excellent IDE support and compile-time error detection

## Supported Providers

### Explicitly Tested (v0.1.0-alpha)

- **OpenAI**: GPT-4o, GPT-4o-mini (Chat, Streaming, Embeddings)
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus/Sonnet/Haiku (Chat, Streaming)
- **Google**: Gemini 2.5 Pro/Flash (Chat, Embeddings)

### Additional Support

Latest 2025 models (e.g., GPT-5, Claude 4, Gemini 3.0) may work via model strings, though not explicitly tested in this release. Please report any issues on [GitHub Issues](https://github.com/gmelli/llm-connectivity/issues).

## Installation

```bash
pip install llm-connectivity
```

## Quick Start

### Basic Usage

```python
from llm_connectivity import LLMClient

# Initialize with OpenAI
client = LLMClient(model="openai/gpt-4o-mini")

# Chat completion
response = client.chat(
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=100
)

print(response.content)        # "Hello! How can I help you today?"
print(response.usage)          # {"prompt_tokens": 10, "completion_tokens": 12, ...}
print(response.cost)           # 0.00003 (in USD)
```

### Provider Switching (<1 Line Change!)

```python
# OpenAI version:
client = LLMClient(model="openai/gpt-4o-mini")
response = client.chat(messages=[{"role": "user", "content": "Hello!"}])

# Google version (ONLY MODEL STRING CHANGES):
client = LLMClient(model="google/models/gemini-2.5-flash")
response = client.chat(messages=[{"role": "user", "content": "Hello!"}])  # SAME CODE!

# Anthropic version (ONLY MODEL STRING CHANGES):
client = LLMClient(model="anthropic/claude-3-haiku-20240307")
response = client.chat(messages=[{"role": "user", "content": "Hello!"}])  # SAME CODE!
```

**That's it!** The same code works across all providers - just change the model string.

## Project Status

**Current Version**: v0.1.0-alpha (Development)

This project is in active development. APIs may change before the v1.0.0 release.

## Documentation

- **[API Reference](docs/api-reference.md)** - Complete class and method documentation
- **[Tutorials](docs/tutorials/)** - Step-by-step guides:
  - [Basic Usage](docs/tutorials/01-basic-usage.md)
  - [Provider Switching](docs/tutorials/02-provider-switching.md)
  - [Error Handling](docs/tutorials/03-error-handling.md)
  - [Streaming](docs/tutorials/04-streaming.md)
  - [Cost Optimization](docs/tutorials/05-cost-optimization.md)
- **[Examples](docs/examples/)** - Working code samples you can copy/paste

## Development

```bash
# Clone repository
git clone https://github.com/gmelli/llm-connectivity.git
cd llm-connectivity

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
black --check .
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. *(Coming Soon)*

## Acknowledgments

Built with insights from the [AGET Framework](https://github.com/aget-framework) research project.
