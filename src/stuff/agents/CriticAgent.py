from src.stuff.ApiController import ApiController, ModelConfig
from src.stuff.agents.AbstractAgent import AbstractAgent, AgentResult
from src.stuff.utils.prompts import CRITIC_AGENT, gen_prompt


class CriticAgent(AbstractAgent):
    def __init__(self, model_config: ModelConfig):
        super().__init__(model_config, role_prompt=CRITIC_AGENT)

    def run(self, input: AgentResult) -> AgentResult:
        print("Running CriticAgent...")
        if hasattr(AgentResult, "metadata"):
            metadata= AgentResult.metadata
        else:
            metadata=None
        prompt = self.role_prompt.format(metadata=metadata)
        full_prompt = gen_prompt(role=prompt, input_data=input.llm_response)
        response = ApiController.execute_prompt(prompt=full_prompt, model_config=self.model_config)
        print("Done CriticAgent!")


        return AgentResult(llm_response=response)
