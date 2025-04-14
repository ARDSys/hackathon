import os
from typing import Literal

import dotenv
from autogen import LLMConfig

dotenv.load_dotenv(override=True)

config = LLMConfig(
    config_list=[
        {
            "model": "gpt-4o-mini",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "tags": ["small", "openai"],
            "price": [0.00015, 0.0006],
        },
        {
            "model": "gpt-4o",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "tags": ["large", "openai"],
            "price": [0.0025, 0.01],
        },
        {
            "model": "o3-mini",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "tags": ["reasoning", "openai"],
            "price": [0.0011, 0.0044],
        },
    ]
)


def get_llm_config(
    model_name: Literal["small", "large", "reasoning"] | str,
) -> LLMConfig:
    """
    Get the LLM config for the given model name.

    Args:
        model_name (str): The name of the model to get the config for.
        Can be "small", "large", "reasoning" or model name like "gpt-4o-mini".

    Returns:
        dict: The LLM config for the given model name.
    """
    try:
        llm_config = config.where(tags=[model_name])
        return llm_config
    except Exception:
        pass

    try:
        llm_config = config.where(model=[model_name])
        return llm_config
    except Exception:
        pass

    raise ValueError(f"No LLM config found for model name: {model_name}")
