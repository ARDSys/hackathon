import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Optional

from agents import Runner
from loguru import logger

from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph
from biohack_attack.hackathon_agents.critic_agent import (
    TriagedHypothesis,
    rheumatology_triage_agent,
)
from biohack_attack.hackathon_agents.hypothesis_agent import (
    hypothesis_agent,
    ScientificHypothesis,
)
from biohack_attack.hackathon_agents.ontology_agent import (
    ontology_agent,
    OntologyAgentOutput,
)
from biohack_attack.model import SubgraphModel


@dataclass
class ProcessConfig:
    num_of_hypotheses: int = 5
    num_of_threads: int = 5
    top_k: int = 3


def run_hypothesis_agent(
    subgraph_model: SubgraphModel, ontology: OntologyAgentOutput
) -> ScientificHypothesis:
    prompt = f"""
# HYPOTHESIS GENERATION TASK

## SUBGRAPH DEFINITION
The following knowledge graph subgraph represents relationships between biomedical entities. Please analyze this structure carefully:

<subgraph>
{subgraph_model.model_dump_json(indent=2)}
</subgraph>

## KEY PATH
Start node: {subgraph_model.start_node}
End node: {subgraph_model.end_node}
Path: {" -> ".join(subgraph_model.path_nodes)}

## CONTEXTUAL ONTOLOGY INFORMATION
The following additional ontological information has been provided to enrich your understanding:

<ontology>
{ontology.model_dump_json(indent=2)}
</ontology>
"""
    return asyncio.run(Runner.run(hypothesis_agent, input=prompt)).final_output


def run_triage_agent(
    hypothesis: ScientificHypothesis,
) -> tuple[ScientificHypothesis, TriagedHypothesis]:
    prompt = f"""
#  HYPOTHESIS ASSESSMENT TASK

## HYPOTHESIS TO EVALUATE
The following scientific hypothesis in rheumatology needs expert evaluation:

<hypothesis>
{hypothesis.model_dump_json(indent=2)}
</hypothesis>
"""
    triage: TriagedHypothesis = asyncio.run(
        Runner.run(rheumatology_triage_agent, input=prompt)
    ).final_output
    return hypothesis, triage


async def run_ontology_agent(subgraph_model: SubgraphModel) -> OntologyAgentOutput:
    ontology_input = f"""
    # ONTOLOGY ENRICHMENT TASK

    ## SUBGRAPH TO ANALYZE
    The following knowledge graph subgraph represents relationships between biomedical entities in rheumatology:

    <subgraph>
    {subgraph_model.model_dump_json(indent=2)}
    </subgraph>

    ## RELATIONSHIP FOCUS
    Start node: {subgraph_model.start_node}
    End node: {subgraph_model.end_node}
    Path nodes: {", ".join(subgraph_model.path_nodes)}
    """
    ontology_result = await Runner.run(ontology_agent, input=ontology_input)
    return ontology_result.final_output


def score_hypothesis(triage: TriagedHypothesis) -> float:
    """
    Calculates a hypothesis score by traversing all fields with 'assessment' in their name
    and multiplying their score and confidence attributes.

    Args:
        triage: An object with assessment fields that have score and confidence attributes

    Returns:
        float: The calculated score
    """
    total_score = 0

    # Get all attributes of the triage object
    for attr_name in dir(triage):
        # Skip private/special attributes and methods
        if attr_name.startswith("_") or callable(getattr(triage, attr_name)):
            continue

        # Check if the attribute name contains 'assessment'
        if "assessment" in attr_name.lower():
            assessment = getattr(triage, attr_name)

            # Check if the assessment has score and confidence attributes
            if hasattr(assessment, "score") and hasattr(assessment, "confidence"):
                total_score += assessment.score * assessment.confidence

    return total_score


async def run_agents(subgraph: Subgraph, config: ProcessConfig) -> Hypothesis:
    subgraph_model = SubgraphModel.from_subgraph(subgraph)

    ontology: OntologyAgentOutput
    logger.info("Enriching subgraph with ontology agent...")
    ontology: OntologyAgentOutput = await run_ontology_agent(subgraph_model)
    logger.debug(ontology.model_dump_json(indent=4))

    logger.info("Generating hypotheses...")
    with ThreadPoolExecutor(max_workers=config.num_of_threads) as executor:
        futures = [
            executor.submit(run_hypothesis_agent, subgraph_model, ontology)
            for _ in range(config.num_of_hypotheses)
        ]
        hypothesis_results = [future.result() for future in futures]
    logger.info("Hypotheses generated.")

    for hypothesis in hypothesis_results:
        logger.debug(hypothesis)

    logger.info("Triage hypotheses...")
    with ThreadPoolExecutor(max_workers=config.num_of_threads) as executor:
        futures = [
            executor.submit(run_triage_agent, hypothesis)
            for hypothesis in hypothesis_results
        ]
        triage_results = [future.result() for future in futures]
    logger.info("Triage completed.")

    for hypothesis, triage in triage_results:
        logger.debug(triage)
        logger.info(
            f"Triage for {hypothesis.title} has score {score_hypothesis(triage)}"
        )

    logger.info("Scoring hypotheses...")
    scored_hypotheses = [
        (hypothesis, triage, score_hypothesis(triage))
        for hypothesis, triage in triage_results
    ]
    # take top k hypotheses
    scored_hypotheses.sort(key=lambda x: x[2], reverse=True)
    best_hypotheses = scored_hypotheses[: config.top_k]

    return Hypothesis(
        title=best_hypotheses[0][0].title,
        statement=best_hypotheses[0][0].statement,
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
