from typing import Any
from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph
import re

from langchain_core.runnables import RunnableConfig
from langfuse.callback import CallbackHandler

from .graph import hackathon_graph
from .state import HackathonState
from .utils import message_to_dict

langfuse_callback = CallbackHandler()


class HypothesisGenerator(HypothesisGeneratorProtocol):
    def run(self, subgraph: Subgraph) -> Hypothesis:
        context = subgraph.context
        path = subgraph.to_cypher_string(full_graph=False)
        
        print(f"Subgraph path:\n{path}")
        print(f"Subgraph context:\n{context}")

        res: HackathonState = hackathon_graph.invoke(
            {"subgraph": path, "context": context},
            config=RunnableConfig(callbacks=[langfuse_callback], recursion_limit=10),
        )

        title = self.__parse_title(res, subgraph) or ""
        statement = self.__parse_statement(res)
        references = self.__parse_references(res)
        return Hypothesis(
            title=title,
            statement=statement,
            source=subgraph,
            method=self,
            references=references,
            metadata={
                "mechanistic_summaries": res["mechanistic_summaries"],
                "context": res["context"],
                # "novelty": res["novelty"],
                # "feasibility": res["feasibility"],
                # "impact": res["impact"],
                # "critique": res["critique"],
                # "iteration": res["iteration"],
                "messages": [message_to_dict(message) for message in res["messages"]],
            },
        )

    def __parse_title(self, state: HackathonState, subgraph: Subgraph) -> str:
        title = state["title"]
        if title:
            return title
        start_node = subgraph.start_node
        end_node = subgraph.end_node
        return f"Hypothesis for {start_node} -> {end_node}"

    def __parse_statement(self, state: HackathonState) -> str:
        statement_match = re.search(
            r"Hypothesis Statement:(.+?)$", state["statement"], re.DOTALL
        )
        if statement_match:
            return statement_match.group(1)
        return state["statement"]

    def __parse_references(self, state: HackathonState) -> list[str]:
        """Return a list of formatted reference strings."""
        list_of_dicts = state.get("references", [])
        return [
            f"- {ref.get('title', 'Unknown Title')} ({ref.get('year', 'n.d.')}) - {ref.get('source', 'Unknown Source')}"
            for ref in list_of_dicts
        ]

    def __str__(self) -> str:
        return "Hackathon Hypothesis Generator"

    def to_json(self) -> dict[str, Any]:
        return {"type": "HypothesisGenerator"}
