import random
from typing import List

from src.stuff.agents.AbstractAgent import AgentResult
from src.stuff.ApiController import ApiController, ModelConfig, ModelEnum


class ResultsMerger:
    @staticmethod
    def merge(results: List[AgentResult]) -> AgentResult:
        actual_result = results[0]
        for result in results[1:]:
            actual_result = ResultsMerger._merge_bi(actual_result, result)
        return actual_result
    
    @staticmethod
    def _merge_bi(result1: AgentResult, result2: AgentResult) -> AgentResult:
        response = ApiController.execute_prompt(
            f"""
                Take this two hypothesis, choose better one as return it as a result. Don't add any stuff, only compare them and return better.
                            
                Hypothesis 1: {result1.llm_response}

                Hypothesis 2: {result2.llm_response}

            """,
            ModelConfig(ModelEnum.TURBO)
        )
        if "Hypothesis 1" in response:
            return result1
        elif "Hypothesis 2" in response:
            return result2
        else:
            return random.choice([result1, result2])
