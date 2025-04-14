import asyncio
from typing import Any

from agents import Agent, Runner
from pydantic import BaseModel

from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph
from biohack_attack.model_factory import ModelFactory, ModelType


class HypothesisOutput(BaseModel):
    title: str
    statement: str
    reasoning_steps: list[str]


async def run_agents(subgraph: Subgraph) -> Hypothesis:
    hypothesis_agent = Agent(
        name="Hypothesis create",
        instructions=f"Build novel scientific hypothesis based on the provided cypher path",
        model=ModelFactory.build_model(ModelType.GEMINI),
        output_type=HypothesisOutput
    )
    path = subgraph.to_cypher_string(full_graph=False)
    result = await Runner.run(hypothesis_agent, path)
    hypothesis_output: HypothesisOutput = result.final_output

    return Hypothesis(
        title=hypothesis_output.title,
        statement=hypothesis_output.statement,
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
