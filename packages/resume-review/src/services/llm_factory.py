"""Factory for creating LLM clients based on agent roles and configuration.

This module provides LLMClientFactory for instantiating the appropriate LLM client
(Gemini, OpenAI, or Anthropic) based on agent name and model override settings.

Reference: specs/003-multi-model-hybrid/contracts/llm-client-interface.md
"""

from typing import Optional

from src.config.model_config import AGENT_MODEL_MAP, AgentName
from src.services.llm_client import (
    AnthropicClient,
    BaseLLMClient,
    GeminiClient,
    OpenAIClient,
)


def create_gemini_client(api_key: str, model: str) -> GeminiClient:
    """Convenience function to create a GeminiClient directly.

    Args:
        api_key: Google Gemini API key
        model: Model identifier (e.g., "gemini-2.0-flash-exp")

    Returns:
        Configured GeminiClient instance
    """
    return GeminiClient(api_key=api_key, model=model)


class LLMClientFactory:
    """Factory for creating appropriate LLM clients based on agent role.

    Encapsulates model selection logic and provider instantiation.
    """

    @staticmethod
    def create_client(
        agent_name: AgentName,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        override_model: Optional[str] = None,
    ) -> BaseLLMClient:
        """Create LLM client for specified agent.

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
        # Determine provider and model
        if override_model:
            # Override mode: use same model for all agents
            provider = LLMClientFactory._detect_provider_from_model(override_model)
            model_id = override_model
        else:
            # Hybrid mode: use agent-specific model
            model_config = AGENT_MODEL_MAP.get(agent_name)
            if not model_config:
                raise ValueError(f"No model configuration found for agent: {agent_name}")
            provider = model_config["provider"]
            model_id = model_config["model_id"]

        # Validate API key is available
        LLMClientFactory._validate_api_key(provider, gemini_api_key, openai_api_key, anthropic_api_key)

        # Instantiate appropriate client
        if provider == "gemini":
            if not gemini_api_key:
                raise ValueError("Gemini API key is required but not provided")
            return GeminiClient(api_key=gemini_api_key, model=model_id)

        elif provider == "openai":
            if not openai_api_key:
                raise ValueError("OpenAI API key is required but not provided")
            return OpenAIClient(api_key=openai_api_key, model=model_id)

        elif provider == "anthropic":
            if not anthropic_api_key:
                raise ValueError("Anthropic API key is required but not provided")
            return AnthropicClient(api_key=anthropic_api_key, model=model_id)

        else:
            raise ValueError(f"Unknown provider: {provider}")

    @staticmethod
    def _detect_provider_from_model(model: str) -> str:
        """Detect provider from model identifier.

        Args:
            model: Model identifier (e.g., "gemini-3.0-flash", "o3-mini")

        Returns:
            Provider name ("gemini", "openai", "anthropic")

        Raises:
            ValueError: If model format is not recognized
        """
        model_lower = model.lower()

        if "gemini" in model_lower:
            return "gemini"
        elif model_lower.startswith("o") and ("-mini" in model_lower or "-preview" in model_lower):
            # OpenAI o-series models: o3-mini, o4-mini, o3-preview, etc.
            return "openai"
        elif "gpt" in model_lower:
            return "openai"
        elif "claude" in model_lower:
            return "anthropic"
        else:
            raise ValueError(
                f"Could not detect provider from model name: {model}. "
                "Supported formats: 'gemini-*', 'o*-mini', 'o*-preview', 'gpt-*', 'claude-*'"
            )

    @staticmethod
    def _validate_api_key(
        provider: str,
        gemini_api_key: Optional[str],
        openai_api_key: Optional[str],
        anthropic_api_key: Optional[str],
    ) -> None:
        """Validate that required API key is available for provider.

        Args:
            provider: Provider name ("gemini", "openai", "anthropic")
            gemini_api_key: Gemini API key (optional)
            openai_api_key: OpenAI API key (optional)
            anthropic_api_key: Anthropic API key (optional)

        Raises:
            ValueError: If required API key is missing
        """
        if provider == "gemini" and not gemini_api_key:
            raise ValueError(
                "Gemini API key is required for this agent but not provided. "
                "Set GEMINI_API_KEY environment variable or pass --gemini-api-key flag."
            )
        elif provider == "openai" and not openai_api_key:
            raise ValueError(
                "OpenAI API key is required for this agent but not provided. "
                "Set OPENAI_API_KEY environment variable or pass --openai-api-key flag."
            )
        elif provider == "anthropic" and not anthropic_api_key:
            raise ValueError(
                "Anthropic API key is required for this agent but not provided. "
                "Set ANTHROPIC_API_KEY environment variable or pass --anthropic-api-key flag."
            )
