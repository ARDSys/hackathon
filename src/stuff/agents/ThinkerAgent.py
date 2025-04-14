from src.stuff.ApiController import ApiController, ModelConfig
from src.stuff.agents.AbstractAgent import AbstractAgent, AgentResult
from src.stuff.utils.prompts import THINKER_AGENT, gen_prompt


class ThinkerAgent(AbstractAgent):
    def __init__(self, model_config: ModelConfig):
        super().__init__(model_config, role_prompt=THINKER_AGENT)

    def run(self, input: AgentResult) -> AgentResult:
        print("Running ThinkerAgent...")
        
        prompt = gen_prompt(role=self.role_prompt, input_data=input.llm_response)
        response = ApiController.execute_prompt(prompt=prompt, model_config=self.model_config)

        print("Done ThinkerAgent!")

        return AgentResult(llm_response=response, hypothesis=input.hypothesis, metadata=input.metadata)
