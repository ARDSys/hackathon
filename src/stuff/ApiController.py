import os
from dataclasses import dataclass
from enum import Enum

import requests
from dotenv import load_dotenv


class ModelEnum(Enum):
    SMALL="gpt-4o-mini"
    LARGE="gpt-4o"
    REASONING="o3-mini"
    TURBO="gpt-3.5-turbo"


@dataclass
class ModelConfig:
    model: ModelEnum


load_dotenv()


class ApiController:
    @staticmethod
    def execute_prompt(prompt: str, model_config: ModelConfig) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model_config.model.value,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        return response.json()["choices"][0]["message"]["content"]
