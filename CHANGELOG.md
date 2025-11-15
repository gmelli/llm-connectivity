# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0-alpha] - 2025-11-14

### Added
- **Chat completion API** with unified interface across providers
  - OpenAI support (GPT-4o, GPT-4o-mini, GPT-3.5-turbo)
  - Anthropic support (Claude 3.5 Sonnet, Claude 3 Opus/Sonnet/Haiku)
  - Google support (Gemini 2.5 Pro/Flash, Gemini 2.0 Flash)
- **Streaming API** for token-by-token responses
  - Consistent StreamChunk format across all providers
  - Real-time progress tracking
- **Embeddings API** (OpenAI and Google only)
  - Text-embedding-3-small/large support (OpenAI)
  - Gemini embedding models support (Google)
- **Provider switching** with <1 line of code change
  - Model string format: `"provider/model-name"`
  - Same code works across all providers (proven in tests)
- **Error handling** with unified exception hierarchy
  - 8 exception types covering all common failure modes
  - Automatic retry with differentiated exponential backoff
  - Rate limit, network, and validation error handling
- **Cost tracking** built-in for all supported models
  - Automatic cost calculation per request
  - Token usage monitoring (prompt, completion, total)
  - Pricing data for all supported models
- **Comprehensive test suite**
  - 97% code coverage (134 tests total)
  - 122 unit tests (100% provider-agnostic)
  - 12 integration tests (real API validation)
  - Provider switching proof (<1 line change verified)
- **Complete documentation**
  - 5 tutorials (basic usage, provider switching, error handling, streaming, cost optimization)
  - 5 working examples (tested, copy/paste ready)
  - Full API reference (10K+ documentation)
  - PyPI-ready README (4.2K enhanced content)
- **CI/CD automation**
  - GitHub Actions workflows (test, lint, publish)
  - Multi-python testing (3.9, 3.10, 3.11, 3.12)
  - Code quality checks (Black, Ruff, mypy)
  - Automated PyPI publishing on release
  - Codecov integration (97% coverage reporting)

### Notes
- This is an **alpha release** - APIs may change before v1.0.0
- Tested models (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5) work reliably
- Newer 2025 models may work via model strings but are not explicitly tested
- Report issues at: https://github.com/gmelli/llm-connectivity/issues

## [0.0.1] - 2025-11-14

### Added
- Initial repository structure
- Project documentation (README, LICENSE)
- Package scaffolding (pyproject.toml, src/ layout)
- MIT License

### Development Setup
- Python 3.9+ support
- Modern packaging with pyproject.toml
- Testing framework (pytest)
- Code quality tools (black, ruff, mypy)

[Unreleased]: https://github.com/gmelli/llm-connectivity/compare/v0.1.0-alpha...HEAD
[0.1.0-alpha]: https://github.com/gmelli/llm-connectivity/compare/v0.0.1...v0.1.0-alpha
[0.0.1]: https://github.com/gmelli/llm-connectivity/releases/tag/v0.0.1
