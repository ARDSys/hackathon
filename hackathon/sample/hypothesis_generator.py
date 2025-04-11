from typing import Any

from ard.hypothesis.hypothesis import Hypothesis
from ard.hypothesis.types import HypothesisGeneratorProtocol
from ard.subgraph.subgraph import Subgraph


class HypothesisGenerator(HypothesisGeneratorProtocol):
    def run(self, subgraph: Subgraph) -> Hypothesis:
        context = subgraph.context
        path = subgraph.to_cypher_string(full_graph=False)

        print(f"Subgraph path:\n{path}")
        print(f"Subgraph context:\n{context}")

        title = "Hypothesis title"
        statement = "Hypothesis statement"
        return Hypothesis(
            title=title,
            statement=statement,
            source=subgraph,
            method=self,
            metadata={},
        )

    def __str__(self) -> str:
        return "HypeGen Generator"

    def to_json(self) -> dict[str, Any]:
        return {"type": "HypothesisGenerator"}
