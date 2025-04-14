import asyncio
from typing import Any

from agents import Runner
from pydantic import BaseModel

from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph
from biohack_attack.hackathon_agents.ontology_agent import ontology_agent, OntologyAgentOutput
from biohack_attack.model import SubgraphModel


class HypothesisOutput(BaseModel):
    title: str
    statement: str
    reasoning_steps: list[str]


async def run_agents(subgraph: Subgraph) -> Hypothesis:
    subgraph_model = SubgraphModel.from_subgraph(subgraph)

    ontology_result = await Runner.run(
        ontology_agent,
        input=subgraph_model
    )
    ontology: OntologyAgentOutput = ontology_result.final_output

    return Hypothesis(
        title="",
        statement="",
        source=subgraph,
        method=HypothesisGenerator(),
    )


class HypothesisGenerator(HypothesisGeneratorProtocol):
    def run(self, subgraph: Subgraph) -> Hypothesis:
        return asyncio.run(run_agents(subgraph))

    def __str__(self) -> str:
        return "HypeGen Generator"

    def to_json(self) -> dict[str, Any]:
        return {"type": "HypothesisGenerator"}
