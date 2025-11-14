# LLM Connectivity

A unified Python interface for multiple Large Language Model providers.

## Overview

`llm-connectivity` provides a consistent, provider-agnostic interface for interacting with LLM APIs from OpenAI, Anthropic, Google, and more. Switch providers with a single line of code while maintaining full feature compatibility.

## Features

- **Unified Interface**: Single API for chat completions and embeddings across all providers
- **Provider Agnostic**: Switch between OpenAI, Anthropic, Google with < 5 lines of code
- **Intelligent Retry**: Differentiated backoff strategies for rate limits, network issues, and validation errors
- **Token Management**: Pre-call estimation and post-call actual token tracking
- **Cost Tracking**: Built-in pricing data for all supported models
- **Exception Handling**: Unified exception hierarchy mapping all provider errors
- **Type Safe**: Full type hints for excellent IDE support

## Supported Providers

- **OpenAI**: GPT-4o, GPT-4, GPT-3.5 (Chat & Embeddings)
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus/Sonnet/Haiku (Chat)
- **Google**: Gemini 1.5 Pro/Flash (Chat & Embeddings)

## Installation

```bash
pip install llm-connectivity
```

## Quick Start

```python
from llm_connectivity import LLMClient

# Initialize with any provider
client = LLMClient(provider="openai", api_key="your-key")

# Chat completion
response = client.chat(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.content)

# Switch providers - same interface!
client = LLMClient(provider="anthropic", api_key="your-key")
response = client.chat(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Project Status

**Current Version**: v0.1.0-alpha (Development)

This project is in active development. APIs may change before the v1.0.0 release.

## Documentation

- [Installation Guide](docs/installation.md) *(Coming Soon)*
- [API Reference](docs/api/index.md) *(Coming Soon)*
- [Examples](examples/) *(Coming Soon)*

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
