import re
from typing import Any

from langchain_core.runnables import RunnableConfig
from langfuse.callback import CallbackHandler

from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph

from .graph import seeding_graph, refinement_graph, eval_graph
from .state import HypgenState
from .utils import message_to_dict

import math

langfuse_callback = CallbackHandler()

class HypothesisProposition:
    def __init__(self, state: HypgenState):
        self.reviews = 0
        self.score = 0
        self.state = state
    
    def ucb(self, total_reviews):
        return self.score + math.sqrt(math.log(total_reviews) / math.max(1, self.reviews))

class HypothesisGenerator(HypothesisGeneratorProtocol):
    
    def evaluate_hypothesis(self, hypothesis_state: HypgenState):
        res: HypgenState = eval_graph.invoke(
            hypothesis_state,
            config=RunnableConfig(callbacks=[langfuse_callback], recursion_limit=100)
        )
        
        return res["score"]
        
    def refine_hypothesis(sefl, hypothesis_state: HypgenState):
        return refine_graph.invoke(
            hypothesis_state,
            config=RunnableConfig(callbacks=[langfuse_callback], recursion_limit=100)
        )
        
    def run(self, subgraph: Subgraph) -> Hypothesis:
        context = subgraph.context
        path = subgraph.to_cypher_string(full_graph=False)
        
        hypothesis_proposals = []
        
        for hyp_ip in range(10):
            # provide previous hypothesis for inovation?
            res: HypgenState = seeding_graph.invoke(
                {"subgraph": path, "context": context},
                config=RunnableConfig(callbacks=[langfuse_callback], recursion_limit=100),
            )
            
            hypothesis_proposals.append(
                HypothesisProposition(
                    res,
                    self.evaluate_hypothesis(res)
                )
            )
            
        for refinement_iter in range(15):
            best_ucb = -1e9
            best_idx = -1
            for i in range(len(hypothesis_proposals)):
                hypothesis = hypothesis_proposals[i]
                
                ucb = hypothesis.ucb()
                if best_idx == -1 or best_ucb < ucb:
                    best_idx = i
                    best_ucb = ucb

            hypothesis = hypothesis[best_idx]            
            hypothesis.state = self.refine_hypothesis(hypothesis)
            hypothesis.score = self.evaluate_hypothesis(hypothesis)
            
            hypothesis[best_idx] = hypothesis
    
        best_hypothesis = None
        for i in range(len(hypothesis_proposals)):
            hypothesis = hypothesis_proposals[i]
            
            if best_hypothesis == None or best_hypothesis.reviews < hypothesis.reviews:
                best_hypothesis = hypothesis
        
        title = self.__parse_title(best_hypothesis.state)
        statement = self.__parse_statement(best_hypothesis.state)
        references = self.__parse_references(best_hypothesis.state)
                    
        return Hypothesis(
            title=title,
            statement=statement,
            source=subgraph,
            method=self,
            references=references,
            metadata={
                "summary": res["summary"],
                "context": res["context"],
                "novelty": res["novelty"],
                "feasibility": res["feasibility"],
                "impact": res["impact"],
                "critique": res["critique"],
                "iteration": res["iteration"],
                "messages": [message_to_dict(message) for message in res["messages"]],
            },
        )

    def __parse_title(self, state: HypgenState, subgraph: Subgraph) -> str:
        title = state["title"]
        if title:
            return title
        start_node = subgraph.start_node
        end_node = subgraph.end_node
        return f"Hypothesis for {start_node} -> {end_node}"

    def __parse_statement(self, state: HypgenState) -> str:
        statement_match = re.search(
            r"Hypothesis Statement:(.+?)$", state["hypothesis"], re.DOTALL
        )
        if statement_match:
            return statement_match.group(1)
        return state["hypothesis"]

    def __parse_references(self, state: HypgenState) -> list[str]:
        return state.get("references", [])

    def __str__(self) -> str:
        return "HypeGen Generator"

    def to_json(self) -> dict[str, Any]:
        return {"type": "HypothesisGenerator"}
