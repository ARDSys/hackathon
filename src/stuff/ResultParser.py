from typing import Any, Dict

# from .hypothesis.hypothesis import Hypothesis
from src.stuff.agents.AbstractAgent import AgentResult


class ResultParser:
    @staticmethod
    def parse_subgraph(subgraph: Any = None) -> AgentResult:
        if subgraph is None:
            return AgentResult(llm_response="Sugar is bad!")  # example
        
        res = ""
        for element in subgraph:
            res += f"{element[0]} {element[1]} {element[2]} and \n"
        res = res[:-4]  # Remove the last " and \n"
            
        return AgentResult(llm_response=res)

    @staticmethod
    def parse_result(result: AgentResult):
        return AgentResult.llm_response
