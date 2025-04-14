from hackathon.autogen.llm_config import get_llm_config
from autogen import ConversableAgent
from typing import Optional
from hackathon.modules.Module import Module

# Navitagte to hackathon/autogen/llm_config.py to configure the LLMs

class DummyAgent(ConversableAgent):
    def __init__(self, name: str):
        super().__init__(name=name, system_message="")

class LLMChatModule(Module):
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

        self.agent = ConversableAgent(
            name=self.agent_name,
            llm_config=self.config,
            system_message=self.system_message,
            description=self.description,
            code_execution_config=False,
        )

        self.sender = DummyAgent("user")

    def forward(self, prompt: str) -> str:
        message = {"role": "user", "content": prompt}
        
        self.agent.receive(message, sender=self.sender, request_reply=True)
        response = self.agent.chat_messages[self.sender][-1]

        return response['content']

