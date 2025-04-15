import re
from typing import Any

from langchain_core.runnables import RunnableConfig
from langfuse.callback import CallbackHandler

from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph

from .graph import hypgen_graph
from .state import HypgenState
from .utils import message_to_dict

langfuse_callback = CallbackHandler()


class HypothesisGenerator(HypothesisGeneratorProtocol):
    def run(self, subgraph: Subgraph) -> Hypothesis:
        context = subgraph.context
        path = subgraph.to_cypher_string(full_graph=False)

        res: HypgenState = hypgen_graph.invoke(
            {"subgraph": path, "context": context},
            config=RunnableConfig(callbacks=[langfuse_callback], recursion_limit=100),
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
                **{key: value for key, value in res.items()},
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
