"""LLM client abstraction layer for multi-provider support.

This module provides a unified interface for interacting with different LLM providers
(Gemini, OpenAI, Anthropic) through a common BaseLLMClient abstraction.

Reference: specs/003-multi-model-hybrid/contracts/llm-client-interface.md
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from anthropic import AsyncAnthropic
from google import genai
from google.genai import types
from openai import AsyncOpenAI


@dataclass
class LLMResponse:
    """Unified response format from any LLM provider.

    All provider implementations MUST return this exact structure.

    Attributes:
        content: Generated text from the model
        model: Model identifier (e.g., "gemini-3.0-flash")
        input_tokens: Number of tokens in the input prompt
        output_tokens: Number of tokens in the generated response
        provider: Provider name ("gemini", "openai", "anthropic")
    """

    content: str
    model: str
    input_tokens: int
    output_tokens: int
    provider: str


class BaseLLMClient(ABC):
    """Abstract base class for LLM provider clients.

    All concrete implementations MUST implement generate_async().
    Agents use this interface without knowing the specific provider.
    """

    @property
    @abstractmethod
    def provider(self) -> str:
        """Get provider name."""
        pass

    def __init__(self, api_key: str, model: str) -> None:
        """Initialize client with API credentials.

        Args:
            api_key: Provider API key
            model: Model identifier (provider-specific format)

        Raises:
            ValueError: If api_key is empty
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        self.api_key = api_key
        self.model = model

    async def generate_async(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate content asynchronously.

        Args:
            system_prompt: System-level instructions (role definition)
            user_prompt: User message (resume content + instructions)
            max_tokens: Maximum tokens to generate (default: 2000)
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)

        Returns:
            LLMResponse with generated content and token counts

        Raises:
            ValueError: If prompts are empty
            RuntimeError: If API call fails after retries
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close underlying client resources."""
        pass


class GeminiClient(BaseLLMClient):
    """Google Gemini API client implementation."""

    def __init__(self, api_key: str, model: str = "gemini-3.0-flash") -> None:
        """Initialize Gemini client.

        Args:
            api_key: Google API key
            model: Gemini model identifier (default: gemini-3.0-flash)

        Raises:
            ValueError: If api_key is empty
        """
        if not api_key:
            raise ValueError("Gemini API key cannot be empty")

        self.client = genai.Client(api_key=api_key)
        self.model = model

    @property
    def provider(self) -> str:
        """Get provider name."""
        return "gemini"

    async def generate_async(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate content using Gemini API.

        Provider-specific notes:
        - system_prompt mapped to config.system_instruction
        - Token usage from response.usage_metadata

        Args:
            system_prompt: System-level instructions
            user_prompt: User message
            max_tokens: Maximum output tokens
            temperature: Sampling temperature

        Returns:
            LLMResponse with generated content

        Raises:
            ValueError: If prompts are empty
            RuntimeError: If API call fails
        """
        if not system_prompt or not user_prompt:
            raise ValueError("Prompts cannot be empty")

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
            temperature=temperature,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model, contents=user_prompt, config=config
        )

        # Handle potential None for usage_metadata
        input_tokens = 0
        output_tokens = 0
        if response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count or 0
            output_tokens = response.usage_metadata.candidates_token_count or 0

        return LLMResponse(
            content=response.text or "",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider=self.provider,
        )

    async def close(self) -> None:
        """Close Gemini client resources."""
        # Cleanly close the underlying aiohttp session if accessible
        try:
            # Check for direct access to aio.client_session if it exists in this version
            if hasattr(self.client, "aio"):
                if hasattr(self.client.aio, "client_session"):
                     await self.client.aio.client_session.close()
                elif hasattr(self.client.aio, "_client_session"):
                     await self.client.aio._client_session.close()
            
            # Also try standard close if available
            if hasattr(self.client, "close"):
                 await self.client.close() if asyncio.iscoroutinefunction(self.client.close) else self.client.close()
        except Exception:
             pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client implementation."""

    def __init__(self, api_key: str, model: str = "o3-mini") -> None:
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            model: OpenAI model identifier (default: o3-mini)

        Raises:
            ValueError: If api_key is empty
        """
        if not api_key:
            raise ValueError("OpenAI API key cannot be empty")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    @property
    def provider(self) -> str:
        """Get provider name."""
        return "openai"

    async def generate_async(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate content using OpenAI API.

        Provider-specific notes:
        - system_prompt as first message with role="system"
        - user_prompt as second message with role="user"
        - Token usage from response.usage

        Args:
            system_prompt: System-level instructions
            user_prompt: User message
            max_tokens: Maximum output tokens
            temperature: Sampling temperature

        Returns:
            LLMResponse with generated content

        Raises:
            ValueError: If prompts are empty
            RuntimeError: If API call fails
        """
        if not system_prompt or not user_prompt:
            raise ValueError("Prompts cannot be empty")

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        tokens_in = 0
        tokens_out = 0
        if response.usage:
            tokens_in = response.usage.prompt_tokens
            tokens_out = response.usage.completion_tokens

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=self.model,
            input_tokens=tokens_in,
            output_tokens=tokens_out,
            provider=self.provider,
        )

    async def close(self) -> None:
        """Close OpenAI client."""
        await self.client.close()


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client implementation."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929") -> None:
        """Initialize Anthropic client.

        Args:
            api_key: Anthropic API key
            model: Claude model identifier (default: claude-sonnet-4-5-20250929)

        Raises:
            ValueError: If api_key is empty
        """
        if not api_key:
            raise ValueError("Anthropic API key cannot be empty")

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    @property
    def provider(self) -> str:
        """Get provider name."""
        return "anthropic"

    async def generate_async(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate content using Anthropic API.

        Provider-specific notes:
        - system_prompt as separate system parameter
        - user_prompt as message with role="user"
        - Token usage from response.usage (includes cache tokens)

        Args:
            system_prompt: System-level instructions
            user_prompt: User message
            max_tokens: Maximum output tokens
            temperature: Sampling temperature

        Returns:
            LLMResponse with generated content

        Raises:
            ValueError: If prompts are empty
            RuntimeError: If API call fails
        """
        if not system_prompt or not user_prompt:
            raise ValueError("Prompts cannot be empty")

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Include cache tokens in input count
        input_tokens = (
            response.usage.input_tokens
            + (getattr(response.usage, 'cache_creation_input_tokens', 0) or 0)
            + (getattr(response.usage, 'cache_read_input_tokens', 0) or 0)
        )

        from anthropic.types import TextBlock
        content_text = ""
        for block in response.content:
            if isinstance(block, TextBlock):
                content_text += block.text

        return LLMResponse(
            content=content_text,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=response.usage.output_tokens,
            provider=self.provider,
        )

    async def close(self) -> None:
        """Close Anthropic client."""
        await self.client.close()
