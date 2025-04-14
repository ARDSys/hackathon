import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Optional

from agents import Runner, trace

from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph
from biohack_attack.hackathon_agents.hypothesis_agent import hypothesis_agent
from biohack_attack.hackathon_agents.ontology_agent import ontology_agent, OntologyAgentOutput
from biohack_attack.model import SubgraphModel
from loguru import logger


@dataclass
class ProcessConfig:
    num_of_hypotheses: int = 1


async def run_agents(subgraph: Subgraph, config: ProcessConfig) -> Hypothesis:
    subgraph_model = SubgraphModel.from_subgraph(subgraph)

    ontology: OntologyAgentOutput
    with trace("Ontology enrichment"):
        logger.info("Enriching subgraph with ontology agent...")
        ontology_result = await Runner.run(
            ontology_agent,
            input=subgraph_model.model_dump_json()
        )
        ontology: OntologyAgentOutput = ontology_result.final_output

    def run_hypothesis_agent():
        return asyncio.run(Runner.run(hypothesis_agent, input=ontology.model_dump_json()))

    logger.info("Generating hypotheses...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_hypothesis_agent) for _ in range(config.num_of_hypotheses)]
        hypothesis_results = [future.result() for future in futures]
    logger.info("Hypotheses generated.")
    best_hypothesis = hypothesis_results[0].final_output

    return Hypothesis(
        title=best_hypothesis.title,
        statement=best_hypothesis.statement,
        source=subgraph,
        method=HypothesisGenerator(),
    )


class HypothesisGenerator(HypothesisGeneratorProtocol):
    def __init__(self, config: Optional[ProcessConfig] = None):
        self.config = config or ProcessConfig()

    def run(self, subgraph: Subgraph) -> Hypothesis:
        return asyncio.run(run_agents(subgraph, self.config))

    def __str__(self) -> str:
        return "HypeGen Generator"

    def to_json(self) -> dict[str, Any]:
        return {"type": "HypothesisGenerator"}
