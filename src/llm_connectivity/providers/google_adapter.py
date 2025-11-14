"""
Google AI Chat API Adapter

Pattern: Different API structure from OpenAI/Anthropic (L002 research)
Purpose: Provider-specific implementation with unified interface

Key Differences:
1. Method naming: generate_content() vs chat.completions.create()
2. Message format: Single string vs structured messages
3. Response structure: Different from OpenAI/Anthropic
4. Model naming: "models/gemini-2.5-pro" (with models/ prefix)
5. No built-in token tracking (need to estimate)

Design Principles:
- Map unified interface → Google's generate_content()
- Convert structured messages → single prompt string
- Estimate tokens (Google doesn't provide detailed tracking)
- Map all exceptions to unified hierarchy
"""
import os
from typing import List, Dict, Any, Optional, Iterator, Union
from dataclasses import dataclass

import google.generativeai as genai

from llm_connectivity.errors import map_google_exception, LLMError
from llm_connectivity.retry import retry_with_backoff


@dataclass
class ChatResponse:
    """Unified chat response format (same as OpenAI/Anthropic adapters)."""
    content: str
    model: str
    usage: Dict[str, int]  # {prompt_tokens, completion_tokens, total_tokens}
    cost: Optional[float]
    provider: str = "google"
    raw_response: Optional[Any] = None


@dataclass
class StreamChunk:
    """Streaming response chunk (same as OpenAI/Anthropic adapters)."""
    content: str
    finish_reason: Optional[str] = None
    raw_chunk: Optional[Any] = None


@dataclass
class EmbeddingResponse:
    """Unified embedding response format (same as OpenAI/Anthropic adapters)."""
    embeddings: List[List[float]]
    model: str
    usage: Dict[str, int]  # {prompt_tokens, total_tokens}
    cost: Optional[float]
    provider: str = "google"
    raw_response: Optional[Any] = None


class GoogleAdapter:
    """Google AI Chat API adapter with unified interface.

    Usage:
        # Basic usage
        adapter = GoogleAdapter(api_key="AIza...")
        response = adapter.chat(
            messages=[{"role": "user", "content": "Hello"}],
            model="models/gemini-2.5-pro"
        )

        # Streaming
        for chunk in adapter.chat_stream(messages=[...], model="models/gemini-2.5-pro"):
            print(chunk.content, end="")
    """

    # Chat pricing per 1M tokens (as of 2025-11-14)
    # Source: https://ai.google.dev/pricing
    PRICING = {
        "gemini-2.5-pro": {"prompt": 1.25, "completion": 5.00},
        "gemini-2.5-flash": {"prompt": 0.075, "completion": 0.30},
        "gemini-2.0-flash": {"prompt": 0.075, "completion": 0.30},
        "gemini-pro-latest": {"prompt": 0.50, "completion": 1.50},  # Alias
    }

    # Embeddings pricing per 1M tokens (as of 2025-11-14)
    # Source: https://ai.google.dev/pricing
    EMBEDDING_PRICING = {
        "text-embedding-004": 0.00001,  # Free tier (up to 1M tokens/day)
        "embedding-001": 0.00001,  # Legacy model (free tier)
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 60.0
    ):
        """Initialize Google AI adapter.

        Args:
            api_key: Google AI API key (defaults to GOOGLE_AI_API_KEY env var)
            timeout: Request timeout in seconds

        Note: Google AI SDK doesn't support base_url or max_retries like OpenAI/Anthropic
        """
        api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_AI_API_KEY not set")

        genai.configure(api_key=api_key)
        self.timeout = timeout

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert structured messages to single prompt string.

        Google's generate_content() expects a single string prompt,
        not structured messages like OpenAI/Anthropic.

        Args:
            messages: Chat messages [{"role": "user", "content": "..."}]

        Returns:
            Single prompt string

        Example:
            [{"role": "system", "content": "You are helpful"},
             {"role": "user", "content": "Hello"}]
            →
            "You are helpful\n\nUser: Hello"
        """
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                parts.append(content)
            elif role == "user":
                parts.append(f"User: {content}")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")

        return "\n\n".join(parts)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Simple heuristic: ~4 chars per token (rough approximation)

        Args:
            text: Input text

        Returns:
            Estimated token count

        Note: Google doesn't provide built-in token counting like OpenAI/Anthropic
        """
        return len(text) // 4

    def _calculate_cost(self, usage: Dict[str, int], model: str) -> Optional[float]:
        """Calculate cost for request.

        Args:
            usage: Token usage dict {prompt_tokens, completion_tokens, total_tokens}
            model: Model name

        Returns:
            Cost in USD, or None if pricing unavailable
        """
        # Normalize model name (remove models/ prefix)
        base_model = model.replace("models/", "")

        # Check if model matches known pricing
        for known_model in self.PRICING.keys():
            if known_model in base_model:
                base_model = known_model
                break

        pricing = self.PRICING.get(base_model)
        if not pricing:
            return None

        # Google pricing is per 1M tokens (like Anthropic)
        prompt_cost = (usage["prompt_tokens"] / 1_000_000) * pricing["prompt"]
        completion_cost = (usage["completion_tokens"] / 1_000_000) * pricing["completion"]

        return prompt_cost + completion_cost

    @retry_with_backoff
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "models/gemini-2.5-pro",
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        **kwargs
    ) -> ChatResponse:
        """Send chat completion request.

        Args:
            messages: Chat messages [{"role": "user", "content": "..."}]
            model: Model name (e.g., "models/gemini-2.5-pro")
            max_tokens: Maximum completion tokens (mapped to max_output_tokens)
            temperature: Sampling temperature (0-2, Google supports 0-2 like OpenAI)
            **kwargs: Additional parameters passed to Google AI API

        Returns:
            ChatResponse with unified format

        Raises:
            LLMError: On API errors (mapped to unified hierarchy)

        Note: Google API is quite different from OpenAI/Anthropic
        """
        # Convert messages to single prompt
        prompt = self._messages_to_prompt(messages)

        # Pre-request token estimation
        estimated_tokens = self._estimate_tokens(prompt)
        print(f"  Estimated prompt tokens: {estimated_tokens}")

        try:
            # Create model instance
            gemini_model = genai.GenerativeModel(model)

            # Prepare generation config
            generation_config = {
                "temperature": temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens

            # Configure safety settings (less restrictive for testing)
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            # Call Google AI API
            response = gemini_model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
                **kwargs
            )

            # Extract response (handle blocked/empty responses)
            try:
                content = response.text
            except (ValueError, AttributeError) as e:
                # Response blocked by safety filters or no valid parts
                # Check if response has candidates
                if hasattr(response, 'candidates') and response.candidates:
                    # Response was blocked, return finish reason
                    finish_reason = response.candidates[0].finish_reason
                    content = f"[Response blocked by Google safety filters: finish_reason={finish_reason}]"
                else:
                    raise ValueError(f"Google AI returned empty response: {e}")

            # Estimate tokens (Google doesn't provide detailed tracking)
            completion_tokens = self._estimate_tokens(content)
            usage = {
                "prompt_tokens": estimated_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": estimated_tokens + completion_tokens
            }

            # Calculate cost
            cost = self._calculate_cost(usage, model)

            return ChatResponse(
                content=content,
                model=model,  # Google doesn't return model in response
                usage=usage,
                cost=cost,
                provider="google",
                raw_response=response
            )

        except Exception as e:
            # Map to unified exception hierarchy
            raise map_google_exception(e)

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "models/gemini-2.5-pro",
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        **kwargs
    ) -> Iterator[StreamChunk]:
        """Send streaming chat completion request.

        Args:
            messages: Chat messages
            model: Model name
            max_tokens: Maximum completion tokens
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Yields:
            StreamChunk for each delta

        Raises:
            LLMError: On API errors (mapped to unified hierarchy)

        Note: Google's streaming is similar to OpenAI (simple iterator)
        """
        # Convert messages to single prompt
        prompt = self._messages_to_prompt(messages)

        # Pre-request token estimation
        estimated_tokens = self._estimate_tokens(prompt)
        print(f"  Estimated prompt tokens: {estimated_tokens}")

        try:
            # Create model instance
            gemini_model = genai.GenerativeModel(model)

            # Prepare generation config
            generation_config = {
                "temperature": temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens

            # Configure safety settings (less restrictive for testing)
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            # Call Google AI streaming API
            response = gemini_model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
                stream=True,
                **kwargs
            )

            # Yield chunks as simple iterator
            for chunk in response:
                if chunk.text:
                    yield StreamChunk(
                        content=chunk.text,
                        finish_reason=None,
                        raw_chunk=chunk
                    )

            # Final chunk
            yield StreamChunk(
                content="",
                finish_reason="stop",
                raw_chunk=None
            )

        except Exception as e:
            # Map to unified exception hierarchy
            raise map_google_exception(e)

    def _calculate_embedding_cost(self, usage: Dict[str, int], model: str) -> Optional[float]:
        """Calculate cost for embeddings request.

        Args:
            usage: Token usage dict {prompt_tokens, total_tokens}
            model: Model name

        Returns:
            Cost in USD, or None if pricing unavailable
        """
        # Normalize model name (remove models/ prefix)
        base_model = model.replace("models/", "")

        # Check if model matches known pricing
        for known_model in self.EMBEDDING_PRICING.keys():
            if known_model in base_model:
                base_model = known_model
                break

        pricing = self.EMBEDDING_PRICING.get(base_model)
        if not pricing:
            return None

        # Google embeddings pricing is per 1M tokens
        return (usage["prompt_tokens"] / 1_000_000) * pricing

    @retry_with_backoff
    def embed(
        self,
        texts: Union[str, List[str]],
        model: str = "models/text-embedding-004",
        **kwargs
    ) -> EmbeddingResponse:
        """Generate embeddings for text(s).

        Args:
            texts: Single text string or list of text strings
            model: Embedding model name (e.g., "models/text-embedding-004")
            **kwargs: Additional parameters passed to Google AI API

        Returns:
            EmbeddingResponse with unified format

        Raises:
            LLMError: On API errors (mapped to unified hierarchy)

        Example:
            # Single text
            response = adapter.embed("Hello world")
            embedding = response.embeddings[0]  # List[float]

            # Batch processing
            response = adapter.embed(["Text 1", "Text 2", "Text 3"])
            embeddings = response.embeddings  # List[List[float]]

        Note: Google's embed_content() handles batches natively
        """
        # Normalize input to list
        is_single = isinstance(texts, str)
        input_texts = [texts] if is_single else texts

        # Estimate tokens (Google doesn't provide token tracking for embeddings)
        estimated_tokens = sum(self._estimate_tokens(text) for text in input_texts)
        print(f"  Estimated prompt tokens: {estimated_tokens}")

        try:
            # Call Google AI Embeddings API
            result = genai.embed_content(
                model=model,
                content=input_texts,
                **kwargs
            )

            # Extract embeddings
            # Google returns dict with 'embedding' key (not 'embeddings')
            # Structure depends on input:
            #   - Single text: {'embedding': [float, float, ...]}  (flat list)
            #   - Batch texts: {'embedding': [[float, ...], [float, ...], ...]}  (list of lists)
            embedding = result.get('embedding', [])

            # Check if this is a batch (list of lists) or single (flat list)
            if embedding and isinstance(embedding[0], list):
                # Batch: already in correct format
                embeddings = embedding
            elif embedding:
                # Single: wrap in list
                embeddings = [embedding]
            else:
                embeddings = []

            # Estimate usage (Google doesn't provide actual token counts)
            usage = {
                "prompt_tokens": estimated_tokens,
                "total_tokens": estimated_tokens
            }

            # Calculate cost
            cost = self._calculate_embedding_cost(usage, model)

            return EmbeddingResponse(
                embeddings=embeddings,
                model=model,
                usage=usage,
                cost=cost,
                provider="google",
                raw_response=result
            )

        except Exception as e:
            # Map to unified exception hierarchy
            raise map_google_exception(e)

    def __repr__(self):
        return f"GoogleAdapter(model=google, timeout={self.timeout})"
