from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from src.stuff.ApiController import ModelConfig


@dataclass
class AgentResult:
    llm_response: str = ""
    stop: bool = False
    metadata: dict = field(default_factory=lambda: {})
    hypothesis: str = ""


class AbstractAgent(ABC):
    def __init__(self, model_config: ModelConfig, role_prompt: str):
        self.model_config = model_config
        self.role_prompt = role_prompt

    @abstractmethod
    def run(self, input: AgentResult) -> AgentResult:
        pass
