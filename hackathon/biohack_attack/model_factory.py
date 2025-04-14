import enum
import os
from typing import Optional, Dict, Any
from venv import logger

from agents import OpenAIChatCompletionsModel, ModelSettings, ModelTracing, trace
from loguru import logger
from openai import AsyncOpenAI



class ModelType(enum.Enum):
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class ModelFactory:
    """
    Factory class to build configurable AI model instances for different providers.

    This factory simplifies the creation of model configurations compatible with
    the 'agents' library structure, supporting Gemini, Anthropic, and OpenAI.
    """

    # Default base URLs and model names (can be overridden)
    _DEFAULT_CONFIG = {
        ModelType.GEMINI: {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model_name": "gemini-2.5-pro-preview-03-25",  # Example default
            "api_key_env": "GEMINI_API_KEY",
        },
        ModelType.ANTHROPIC: {
            "base_url": "https://api.anthropic.com/v1/",
            "model_name": "claude-3.7-sonnet-20250219",  # Example default
            "api_key_env": "ANTHROPIC_API_KEY",
        },
        ModelType.OPENAI: {
            "base_url": None,  # Standard OpenAI client uses default base URL
            "model_name": "gpt-4o",  # Example default
            "api_key_env": "OPENAI_API_KEY",
        },
    }

    @staticmethod
    def build_model(
            model_type: ModelType,
            api_key: Optional[str] = None,
            model_name: Optional[str] = None,
            base_url: Optional[str] = None,
            client_kwargs: Optional[Dict[str, Any]] = None,
    ) -> OpenAIChatCompletionsModel:
        """
        Builds and returns a model configuration instance.

        Args:
            model_type: The type of model provider (ModelType.GEMINI, etc.).
            api_key: The API key for the provider. If None, attempts to read from
                     the corresponding environment variable (e.g., GEMINI_API_KEY).
            model_name: The specific model name (e.g., 'gemini-1.5-flash',
                        'claude-3-opus-20240229', 'gpt-4o'). If None, uses
                        the default for the provider.
            base_url: The base URL for the API endpoint. If None, uses the default
                      for the provider (or none for standard OpenAI).
            client_kwargs: Additional keyword arguments to pass to the
                           AsyncOpenAI client constructor (e.g., timeout, max_retries).

        Returns:
            An instance of OpenAIChatCompletionsModel configured for the specified provider.

        Raises:
            ValueError: If the API key is not provided and cannot be found in the
                        environment variables, or if an invalid model_type is given.
            ImportError: If the 'agents' library or its components cannot be imported.
        """
        if model_type not in ModelFactory._DEFAULT_CONFIG:
            raise ValueError(f"Unsupported model type: {model_type}")

        config = ModelFactory._DEFAULT_CONFIG[model_type]

        # Determine API Key
        resolved_api_key = api_key or os.getenv(config["api_key_env"])
        if not resolved_api_key:
            raise ValueError(
                f"API key for {model_type.value} not provided and "
                f"environment variable '{config['api_key_env']}' not set."
            )

        # Determine Model Name
        resolved_model_name = model_name or config["model_name"]
        if not resolved_model_name:
            raise ValueError(f"Model name for {model_type.value} must be specified.")

        # Determine Base URL (only override if explicitly passed)
        resolved_base_url = base_url if base_url is not None else config["base_url"]

        # Initialize client_kwargs and model_wrapper_kwargs if None
        client_args = client_kwargs or {}

        # Create the AsyncOpenAI client
        # For standard OpenAI, base_url should be None or OpenAI's default
        # The AsyncOpenAI client handles None base_url correctly for default OpenAI API
        logger.debug(f"--- Building Model: {model_type.name} ---")
        logger.debug(f"Model Name: {resolved_model_name}")
        logger.debug(f"Base URL: {resolved_base_url if resolved_base_url else 'Default OpenAI'}")
        logger.debug(f"API Key Source: {'Provided Argument' if api_key else 'Environment Variable'}")
        logger.debug(f"Client Kwargs: {client_args}")
        logger.debug("-" * (len(f"--- Building Model: {model_type.name} ---")))

        client = AsyncOpenAI(
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            **client_args,
        )
        return OpenAIChatCompletionsModel(
            model=resolved_model_name,
            openai_client=client,
        )


