from src.stuff.ApiController import ApiController, ModelConfig
from src.stuff.agents.AbstractAgent import AbstractAgent, AgentResult
from src.stuff.utils.prompts import FEASIBILITY_AGENT, gen_prompt


class FeasibilityAgent(AbstractAgent):
    def __init__(self, model_config: ModelConfig):
        super().__init__(model_config, role_prompt=FEASIBILITY_AGENT)

    def run(self, input: AgentResult) -> AgentResult:
        print("Runnig FeasibilityAgent...")
        prompt = gen_prompt(role=self.role_prompt, input_data=input.llm_response)
        response = ApiController.execute_prompt(prompt=prompt, model_config=self.model_config)
        print("Done FeasibilityAgent!")

        return AgentResult(llm_response=response, hypothesis=input.hypothesis, metadata=input.metadata)
