from src.stuff.ApiController import ApiController, ModelConfig
from src.stuff.agents.AbstractAgent import AbstractAgent, AgentResult
from src.stuff.utils.prompts import HYPOTHESIS_AGENT, gen_prompt


class HypothesisAgent(AbstractAgent):
    def __init__(self, model_config: ModelConfig):
        super().__init__(model_config, role_prompt=HYPOTHESIS_AGENT)

    def run(self, input: AgentResult) -> AgentResult:
        print("Running HypothesisAgent...")

        prompt = gen_prompt(role=self.role_prompt, input_data=input.llm_response)
        response = ApiController.execute_prompt(prompt=prompt, model_config=self.model_config)

        print("Done HypothesisAgent!")

        return AgentResult(llm_response=response, hypothesis=response, metadata=input.metadata)

