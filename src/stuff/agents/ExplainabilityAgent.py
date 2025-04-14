from src.stuff.ApiController import ApiController, ModelConfig
from src.stuff.agents.AbstractAgent import AbstractAgent, AgentResult
from src.stuff.utils.prompts import EXPLAINABILITY_AGENT, gen_prompt


class ExplainableAgent(AbstractAgent):
    def __init__(self, model_config: ModelConfig):
        super().__init__(model_config, role_prompt=EXPLAINABILITY_AGENT)

    """Explainable Agent: This agent expert is responsible for assessing the clarity and interpretability
    of the hypothesis proposed by the Evidence and Feasibility Agents."""

    def run(self, input: AgentResult) -> AgentResult:
        print("Running ExplainableAgent...")
        prompt = gen_prompt(role=self.role_prompt, input_data=input.llm_response)
        response = ApiController.execute_prompt(prompt=prompt, model_config=self.model_config)
        print("Done ExplainableAgent!")

        return AgentResult(llm_response=response, hypothesis=input.hypothesis, metadata=input.metadata)
