"""
Configuration for language models.
"""

import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv(override=True)


class ModelConfig(BaseModel):
    """Base configuration for language models."""

    model_name: str
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    temperature: Optional[float] = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 120
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    additional_kwargs: Dict[str, Any] = Field(default_factory=dict)


class OpenAIConfig(ModelConfig):
    """Configuration for OpenAI models."""

    provider: str = "openai"
    streaming: bool = False


class AnthropicConfig(ModelConfig):
    """Configuration for Anthropic models."""

    provider: str = "anthropic"
    streaming: bool = False


class GeminiConfig(ModelConfig):
    """Configuration for Gemini models."""

    provider: str = "google"
    streaming: bool = False


# Model registry
MODEL_REGISTRY = {
    "small": OpenAIConfig(
        model_name="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
    ),
    "large": OpenAIConfig(
        model_name="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
    ),
    "reasoning": OpenAIConfig(
        model_name="o3-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        additional_kwargs={"reasoning_effort": "high"},
    ),
    "anthropic": AnthropicConfig(
        model_name="claude-3-5-sonnet",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    ),
    "gemmini_2_5": GeminiConfig(
        model_name="gemini-2.5-pro-preview-03-25",
        api_key=os.getenv("GOOGLE_API_KEY"),
    ),
}
