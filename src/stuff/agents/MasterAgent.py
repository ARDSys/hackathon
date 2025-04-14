from typing import List

from src.stuff.ApiController import ApiController, ModelConfig
from src.stuff.ResultsMerger import ResultsMerger
from src.stuff.agents.AbstractAgent import AbstractAgent, AgentResult
from src.stuff.utils.prompts import MASTER_AGENT, gen_prompt


class MasterAgent(AbstractAgent):
    def __init__(self, model_config: ModelConfig, local_agents_number = 3):
        super().__init__(model_config, role_prompt=MASTER_AGENT)
        self._local_agents: List[MasterAgent] = []
        self.spawn_agents(local_agents_number)

    def run(self, input: AgentResult) -> AgentResult:
        print("Running MasterAgent...")

        if self._local_agents:
            result = ResultsMerger.merge([agent.run(input) for agent in self._local_agents])
        else:
            prompt = gen_prompt(role=self.role_prompt, input_data=input.llm_response)
            result = AgentResult(
                llm_response=ApiController.execute_prompt(
                    prompt=prompt,
                    model_config=self.model_config
                )
            )

        print("Done MasterAgent!")

        return result
    
    def spawn_agents(self, agents_number: int):
        for _ in range(agents_number):
            new_agent = MasterAgent(self.model_config, agents_number - 1)
            self._local_agents.append(new_agent)
