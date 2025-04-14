from hackathon.autogen.llm_config import get_llm_config
from autogen import ConversableAgent
from typing import Optional
from hackathon.modules.Module import Module

# Navitagte to hackathon/autogen/llm_config.py to configure the LLMs

class DummyAgent(ConversableAgent):
    def __init__(self, name: str):
        super().__init__(name=name, system_message="")

class LLMQueryModule(Module):
    def __init__(
        self,
        model_name: str = "small",
        agent_name: str = "llm_agent",
        system_message: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.model_name = model_name
        self.config = get_llm_config(model_name)

        self.agent_name = agent_name
        self.system_message = system_message
        self.description = description

    def forward(self, prompt: str) -> str:
        agent = ConversableAgent(
            name=self.agent_name,
            llm_config=self.config,
            system_message=self.system_message,
            description=self.description,
            code_execution_config=False,
        )

        message = {"role": "user", "content": prompt}
        sender = DummyAgent("user")
        agent.receive(message, sender=sender, request_reply=True)
        response = agent.chat_messages[sender][-1]

        return response['content']
