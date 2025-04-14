"""
Utility functions for working with language models.
"""

from typing import Dict, Optional, Union

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseLanguageModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langfuse.callback import CallbackHandler

from .config import (
    MODEL_REGISTRY,
    AnthropicConfig,
    GeminiConfig,
    ModelConfig,
    OpenAIConfig,
)

ModelType = Union[str, ModelConfig, BaseLanguageModel, None]

langfuse_callback = CallbackHandler()


def get_llm(config: ModelConfig) -> BaseLanguageModel:
    """
    Initialize a language model based on the provided configuration.

    Args:
        config: Model configuration

    Returns:
        Initialized language model
    """
    if isinstance(config, OpenAIConfig):
        return ChatOpenAI(
            model_name=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
            streaming=config.streaming,
            openai_api_key=config.api_key,
            openai_api_base=config.api_base,
            callbacks=[langfuse_callback],
            **config.additional_kwargs,
        )
    elif isinstance(config, AnthropicConfig):
        return ChatAnthropic(
            model_name=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            anthropic_api_key=config.api_key,
            callbacks=[langfuse_callback],
            **config.additional_kwargs,
        )
    elif isinstance(config, GeminiConfig):
        return ChatGoogleGenerativeAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            google_api_key=config.api_key,
            callbacks=[langfuse_callback],
            **config.additional_kwargs,
        )
    else:
        raise ValueError(f"Unsupported model provider: {config.provider}")


def get_model_by_name(
    model_name: str, registry: Optional[Dict[str, ModelConfig]] = None, **kwargs
) -> BaseLanguageModel:
    """
    Get a language model by name from the registry.

    Args:
        model_name: Name of the model in the registry
        registry: Custom registry to use (optional)
        **kwargs: Additional parameters to override in the config

    Returns:
        Initialized language model
    """
    registry = registry or MODEL_REGISTRY

    if model_name not in registry:
        raise ValueError(
            f"Model {model_name} not found in registry. Available models: {list(registry.keys())}"
        )

    # Get the base config
    config = registry[model_name]

    # Override with any provided kwargs
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return get_llm(config)


def get_default_model() -> BaseLanguageModel:
    """
    Get the default language model.

    Returns:
        Initialized language model
    """
    return get_model_by_name("small")


def get_model(
    model: ModelType = None,
    registry: Optional[Dict[str, ModelConfig]] = None,
    **kwargs,
) -> BaseLanguageModel:
    """
    Get a language model

    Args:
        model: Model name, config, or instance
        registry: Custom registry to use (optional)
        **kwargs: Additional parameters to override in the config

    Returns:
        Initialized language model
    """
    if model is None:
        return get_default_model()
    elif isinstance(model, str):
        return get_model_by_name(model, registry, **kwargs)
    elif isinstance(model, ModelConfig):
        return get_llm(model)
    elif isinstance(model, BaseLanguageModel):
        return model
    else:
        raise ValueError(f"Unsupported model type: {type(model)}")
