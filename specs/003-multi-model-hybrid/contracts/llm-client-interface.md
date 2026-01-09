# Contract: BaseLLMClient Interface

**Version**: 1.0.0
**Date**: 2026-01-09
**Type**: Abstract Base Class

## Overview

`BaseLLMClient` defines the contract that all LLM provider implementations must fulfill. This enables polymorphic usage of different providers (Gemini, OpenAI, Anthropic) without agent code needing provider-specific logic.

---

## Interface Definition

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMResponse:
    """
    Unified response format from any LLM provider.

    All provider implementations MUST return this exact structure.
    """
    content: str  # Generated text
    model: str  # Model identifier (e.g., "gemini-3.0-flash")
    input_tokens: int  # Tokens in prompt
    output_tokens: int  # Tokens in response
    provider: str  # Provider name ("gemini", "openai", "anthropic")


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM provider clients.

    All concrete implementations MUST implement generate_async().
    """

    def __init__(self, api_key: str, model: str):
        """
        Initialize client with API credentials.

        Args:
            api_key: Provider API key
            model: Model identifier (provider-specific format)

        Raises:
            ValueError: If api_key is empty
            ValueError: If model is not supported by provider
        """
        pass

    @abstractmethod
    async def generate_async(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> LLMResponse:
        """
        Generate content asynchronously.

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
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit exceeded

        Contract Guarantees:
            - content will never be empty (or raises exception)
            - input_tokens >= 0
            - output_tokens > 0 (if successful)
            - provider matches this client's provider name
        """
        pass
```

---

## Concrete Implementations

### GeminiClient

```python
from google import genai
from google.genai import types

class GeminiClient(BaseLLMClient):
    """Google Gemini API client implementation."""

    def __init__(self, api_key: str, model: str = "gemini-3.0-flash"):
        if not api_key:
            raise ValueError("Gemini API key cannot be empty")

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.provider = "gemini"

    async def generate_async(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> LLMResponse:
        """
        Implement using google-genai SDK.

        Provider-specific notes:
        - system_prompt mapped to config.system_instruction
        - Combines consecutive messages into single content
        - Token usage from response.usage_metadata
        """
        if not system_prompt or not user_prompt:
            raise ValueError("Prompts cannot be empty")

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
            temperature=temperature
        )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=config
        )

        return LLMResponse(
            content=response.text,
            model=self.model,
            input_tokens=response.usage_metadata.prompt_token_count,
            output_tokens=response.usage_metadata.response_token_count,
            provider=self.provider
        )
```

### OpenAIClient

```python
from openai import AsyncOpenAI

class OpenAIClient(BaseLLMClient):
    """OpenAI API client implementation."""

    def __init__(self, api_key: str, model: str = "o3-mini"):
        if not api_key:
            raise ValueError("OpenAI API key cannot be empty")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.provider = "openai"

    async def generate_async(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> LLMResponse:
        """
        Implement using openai SDK.

        Provider-specific notes:
        - system_prompt as first message with role="system"
        - user_prompt as second message with role="user"
        - Token usage from response.usage
        """
        if not system_prompt or not user_prompt:
            raise ValueError("Prompts cannot be empty")

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            provider=self.provider
        )
```

### AnthropicClient

```python
from anthropic import AsyncAnthropic

class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client implementation."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        if not api_key:
            raise ValueError("Anthropic API key cannot be empty")

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.provider = "anthropic"

    async def generate_async(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> LLMResponse:
        """
        Implement using anthropic SDK.

        Provider-specific notes:
        - system_prompt as separate system parameter
        - user_prompt as message with role="user"
        - Token usage from response.usage (includes cache tokens)
        """
        if not system_prompt or not user_prompt:
            raise ValueError("Prompts cannot be empty")

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        # Include cache tokens in input count
        input_tokens = (
            response.usage.input_tokens +
            response.usage.cache_creation_input_tokens +
            response.usage.cache_read_input_tokens
        )

        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=response.usage.output_tokens,
            provider=self.provider
        )
```

---

## Factory Contract

```python
class LLMClientFactory:
    """
    Factory for creating appropriate LLM clients based on agent role.

    Encapsulates model selection logic and provider instantiation.
    """

    @staticmethod
    def create_client(
        agent_name: AgentName,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        override_model: Optional[str] = None
    ) -> BaseLLMClient:
        """
        Create LLM client for specified agent.

        Args:
            agent_name: Agent role (RECRUITER, TECHNICAL_WRITER, etc.)
            gemini_api_key: Google Gemini API key
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
            override_model: If set, use this model for all agents

        Returns:
            Configured BaseLLMClient instance

        Raises:
            ValueError: If required API key is missing
            ValueError: If override_model is invalid

        Behavior:
            - If override_model set: Detect provider from model name, use that client
            - If override_model None: Use AGENT_MODEL_MAP to select optimal model

        Examples:
            # Hybrid mode (agent-specific models)
            client = LLMClientFactory.create_client(
                agent_name=AgentName.RECRUITER,
                gemini_api_key="...",
                openai_api_key="...",
                anthropic_api_key="..."
            )
            # Returns: GeminiClient("gemini-3.0-flash")

            # Override mode (all agents use same model)
            client = LLMClientFactory.create_client(
                agent_name=AgentName.RECRUITER,
                anthropic_api_key="...",
                override_model="claude-sonnet-4-5-20250929"
            )
            # Returns: AnthropicClient("claude-sonnet-4-5-20250929")
        """
        pass
```

---

## Contract Validation

### Pre-conditions

**All implementations MUST validate**:
1. API key is non-empty in `__init__()`
2. Model name is valid for provider in `__init__()`
3. Prompts are non-empty in `generate_async()`
4. max_tokens > 0 in `generate_async()`
5. temperature is between 0.0 and 1.0

### Post-conditions

**All implementations MUST guarantee**:
1. `LLMResponse.content` is non-empty (or exception raised)
2. `LLMResponse.input_tokens >= 0`
3. `LLMResponse.output_tokens > 0` (for successful generation)
4. `LLMResponse.provider` matches client's provider name
5. `LLMResponse.model` matches requested model

### Error Handling

**All implementations MUST raise specific exceptions**:

| Condition | Exception Type | Message Format |
|-----------|---------------|----------------|
| Empty API key | `ValueError` | "{Provider} API key cannot be empty" |
| Invalid model | `ValueError` | "Model '{model}' not supported by {provider}" |
| Empty prompt | `ValueError` | "Prompts cannot be empty" |
| Authentication failure | `AuthenticationError` | "{Provider} API key is invalid" |
| Rate limit exceeded | `RateLimitError` | "{Provider} rate limit exceeded, retry after {seconds}s" |
| API unavailable | `RuntimeError` | "{Provider} API failed after {attempts} retries: {error}" |

---

## Usage Contract for Agents

```python
class BaseAgent(ABC):
    """
    Base agent using LLM client.

    Agents MUST use injected llm_client, not construct their own.
    """

    def __init__(self, llm_client: BaseLLMClient, agent_name: AgentName):
        """
        Initialize agent with LLM client.

        Args:
            llm_client: Pre-configured LLM client (injected)
            agent_name: This agent's role identifier

        Contract:
            - Agent does NOT construct clients directly
            - Agent does NOT need to know which provider is being used
            - Agent calls llm_client.generate_async() with prompts
        """
        self.llm_client = llm_client
        self.agent_name = agent_name

    async def evaluate_async(
        self,
        resume: Resume,
        target_role: str
    ) -> Feedback:
        """
        Evaluate resume using injected LLM client.

        Contract guarantees:
            - llm_client will return valid LLMResponse
            - Token usage is tracked automatically by caller
            - No provider-specific code in agent logic
        """
        system_prompt = self.get_system_prompt(target_role)
        user_prompt = self.get_user_prompt(resume)

        # Provider-agnostic call
        response = await self.llm_client.generate_async(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2000
        )

        # Parse response (provider-agnostic)
        return self.parse_feedback(response.content)
```

---

## Testing Contract

### Mock Client for Tests

```python
class MockLLMClient(BaseLLMClient):
    """Mock implementation for unit tests."""

    def __init__(self, api_key: str = "mock-key", model: str = "mock-model"):
        self.api_key = api_key
        self.model = model
        self.provider = "mock"
        self.call_count = 0
        self.last_system_prompt = None
        self.last_user_prompt = None

    async def generate_async(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Return predefined mock response."""
        self.call_count += 1
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt

        return LLMResponse(
            content="Mock evaluation feedback...",
            model=self.model,
            input_tokens=len(system_prompt.split()) + len(user_prompt.split()),
            output_tokens=10,
            provider=self.provider
        )
```

### Contract Verification Tests

```python
import pytest

@pytest.mark.parametrize("client_class", [GeminiClient, OpenAIClient, AnthropicClient])
async def test_client_contract_compliance(client_class):
    """Verify all clients comply with BaseLLMClient contract."""
    client = client_class(api_key="test-key")

    response = await client.generate_async(
        system_prompt="You are a test assistant.",
        user_prompt="Say hello.",
        max_tokens=50
    )

    # Post-condition checks
    assert isinstance(response, LLMResponse)
    assert response.content != ""
    assert response.input_tokens >= 0
    assert response.output_tokens > 0
    assert response.provider in ["gemini", "openai", "anthropic"]
    assert response.model != ""


@pytest.mark.parametrize("client_class", [GeminiClient, OpenAIClient, AnthropicClient])
async def test_empty_api_key_raises(client_class):
    """Verify all clients reject empty API keys."""
    with pytest.raises(ValueError, match="API key cannot be empty"):
        client_class(api_key="")


@pytest.mark.parametrize("client_class", [GeminiClient, OpenAIClient, AnthropicClient])
async def test_empty_prompts_raise(client_class):
    """Verify all clients reject empty prompts."""
    client = client_class(api_key="test-key")

    with pytest.raises(ValueError, match="Prompts cannot be empty"):
        await client.generate_async(system_prompt="", user_prompt="test")

    with pytest.raises(ValueError, match="Prompts cannot be empty"):
        await client.generate_async(system_prompt="test", user_prompt="")
```

---

## Versioning & Compatibility

**Version**: 1.0.0
**Breaking Changes**:
- None (initial version)

**Backward Compatibility**:
- Existing agents using `Anthropic` client directly will be migrated to use `AnthropicClient` (wrapper with same interface)

**Future Extensions** (Non-breaking):
- Add `generate_stream_async()` for streaming responses
- Add `count_tokens()` for pre-call token estimation
- Add `supports_function_calling()` capability detection

---

## Summary

This contract ensures:
1. **Polymorphism**: All providers implement identical interface
2. **Type Safety**: LLMResponse is strongly typed
3. **Error Clarity**: Specific exceptions for specific failures
4. **Testability**: MockLLMClient enables unit testing
5. **Extensibility**: New providers can be added without changing agent code

**Contract Guarantees**:
- ✅ Non-empty content or exception
- ✅ Accurate token counts
- ✅ Provider identification
- ✅ Predictable error handling
- ✅ Async/await support
