from dataclasses import dataclass
from typing import Any, Optional, List, Tuple, Dict
import asyncio
from concurrent.futures import ThreadPoolExecutor
from loguru import logger

from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph
from biohack_attack.hackathon_agents.critic_agent import (
    TriagedHypothesis,
    rheumatology_triage_agent,
)
from biohack_attack.hackathon_agents.decomposition_agent import (
    HypothesisDecomposition,
    hypothesis_decomposer_agent,
)
from biohack_attack.hackathon_agents.hypothesis_agent import (
    hypothesis_agent,
    ScientificHypothesis,
)
from biohack_attack.hackathon_agents.hypothesis_assigment_agent import (
    verify_hypothesis_decomposition,
)
from biohack_attack.hackathon_agents.ontology_agent import (
    ontology_agent,
    OntologyAgentOutput,
)
from biohack_attack.hackathon_agents.verification_agent import HypothesisVerification
from biohack_attack.model import SubgraphModel
from agents import Runner


@dataclass
class ProcessConfig:
    num_of_hypotheses: int = 2
    num_of_threads: int = 5
    top_k: int = 1


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


async def decompose_hypothesis(
    hypothesis: ScientificHypothesis, ontology: OntologyAgentOutput
) -> HypothesisDecomposition:
    """
    Decompose a scientific hypothesis into falsifiable statements.

    Args:
        hypothesis: The scientific hypothesis to decompose
        ontology: Ontology information to enrich understanding

    Returns:
        A HypothesisDecomposition containing falsifiable statements
    """
    prompt = f"""
    # HYPOTHESIS DECOMPOSITION TASK

    Please decompose the following scientific hypothesis into fundamental falsifiable statements:

    ## HYPOTHESIS DETAILS

    Title: {hypothesis.title}

    Statement: {hypothesis.statement}

    Mechanism: {hypothesis.mechanism.pathway_description if hypothesis.mechanism else "Not specified"}

    Expected Outcomes: {", ".join(hypothesis.expected_outcomes) if hypothesis.expected_outcomes else "Not specified"}

    Experimental Approaches: {", ".join(hypothesis.experimental_approaches) if hypothesis.experimental_approaches else "Not specified"}

    ## ONTOLOGY ENRICHMENT
    The following additional ontological information has been provided to enrich your understanding:
    <ontology>
    {ontology.model_dump_json(indent=2)}
    </ontology>
    """

    result = await Runner.run(hypothesis_decomposer_agent, input=prompt)
    return result.final_output


# Wrapper function to run async function in ThreadPoolExecutor
def run_async_in_thread(coro):
    return asyncio.run(coro)


# Wrapper for decompose_hypothesis to use in ThreadPoolExecutor
def decompose_hypothesis_wrapper(hypothesis, ontology):
    return run_async_in_thread(decompose_hypothesis(hypothesis, ontology))


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


async def verify_multiple_hypotheses(
    hypothesis_decompositions: List[Tuple[str, HypothesisDecomposition]],
) -> Dict[str, HypothesisVerification]:
    """
    Verify multiple hypothesis decompositions in parallel.

    Args:
        hypothesis_decompositions: A list of tuples containing (hypothesis_id, decomposition)

    Returns:
        A dictionary mapping hypothesis IDs to their verification results
    """
    if not hypothesis_decompositions:
        logger.warning("No hypothesis decompositions to verify")
        return {}  # Return empty dict to handle the case of empty input

    verification_tasks = {
        hypothesis_id: verify_hypothesis_decomposition(decomposition)
        for hypothesis_id, decomposition in hypothesis_decompositions
    }

    # Run all verification tasks concurrently
    results = {}
    for hypothesis_id, verification_task in verification_tasks.items():
        try:
            result = await verification_task
            results[hypothesis_id] = result
            logger.info(
                f"Verified hypothesis {hypothesis_id} with score {result.verification_score}"
            )
        except Exception as e:
            logger.error(f"Error verifying hypothesis {hypothesis_id}: {str(e)}")

    return results


async def run_agents(subgraph: Subgraph, config: ProcessConfig) -> Hypothesis:
    # Convert the subgraph to a model
    subgraph_model = SubgraphModel.from_subgraph(subgraph)

    # Step 1: Enrich subgraph with ontology agent
    logger.info("Enriching subgraph with ontology agent...")
    ontology: OntologyAgentOutput = await run_ontology_agent(subgraph_model)
    logger.debug(ontology.model_dump_json(indent=4))

    # Step 2: Generate hypotheses using ThreadPoolExecutor
    logger.info("Generating hypotheses...")
    hypothesis_results = []
    with ThreadPoolExecutor(max_workers=config.num_of_threads) as executor:
        futures = [
            executor.submit(run_hypothesis_agent, subgraph_model, ontology)
            for _ in range(config.num_of_hypotheses)
        ]
        for future in futures:
            try:
                hypothesis_results.append(future.result())
            except Exception as e:
                logger.error(f"Error generating hypothesis: {str(e)}")

    if not hypothesis_results:
        raise ValueError("Failed to generate any valid hypotheses")

    logger.info(f"Generated {len(hypothesis_results)} hypotheses.")

    # Step 3: Triage hypotheses using ThreadPoolExecutor
    logger.info("Triage hypotheses...")
    triage_results = []
    with ThreadPoolExecutor(max_workers=config.num_of_threads) as executor:
        futures = [
            executor.submit(run_triage_agent, hypothesis)
            for hypothesis in hypothesis_results
        ]
        for future in futures:
            try:
                triage_results.append(future.result())
            except Exception as e:
                logger.error(f"Error triaging hypothesis: {str(e)}")

    if not triage_results:
        raise ValueError("Failed to triage any hypotheses")

    logger.info(f"Triage completed for {len(triage_results)} hypotheses.")

    # Step 4: Score hypotheses and select top ones
    logger.info("Scoring hypotheses...")
    scored_hypotheses = [
        (hypothesis, triage, score_hypothesis(triage))
        for hypothesis, triage in triage_results
    ]
    scored_hypotheses.sort(key=lambda x: x[2], reverse=True)

    # Select top k hypotheses
    top_k = min(config.top_k, len(scored_hypotheses))
    best_hypotheses = scored_hypotheses[:top_k]

    logger.info(f"Selected top {top_k} hypotheses for further processing.")

    # Step 5: Decompose hypotheses using ThreadPoolExecutor with wrapper function
    logger.info("Decomposing hypotheses...")
    decomposition_results = []
    with ThreadPoolExecutor(max_workers=config.num_of_threads) as executor:
        futures = [
            executor.submit(decompose_hypothesis_wrapper, hypothesis, ontology)
            for hypothesis, _, _ in best_hypotheses
        ]
        # Collect results, handle any exceptions
        for future in futures:
            try:
                decomposition_results.append(future.result())
            except Exception as e:
                logger.error(f"Error decomposing hypothesis: {str(e)}")

    logger.info(f"Decomposition completed for {len(decomposition_results)} hypotheses.")

    # Step 6: Verify decomposed hypotheses
    logger.info("Verifying decomposed hypotheses...")
    hypothesis_decompositions = [
        (f"hypothesis_{i}", decomposition)
        for i, decomposition in enumerate(decomposition_results)
    ]

    verification_results = await verify_multiple_hypotheses(hypothesis_decompositions)
    logger.info(f"Verification completed for {len(verification_results)} hypotheses.")

    verification_metadata = {
        hypothesis_id: {
            "verification_score": verification.verification_score,
            "overall_assessment": verification.overall_assessment,
            "statement_verifications": [
                {
                    "statement": sv.statement,
                    "verification_conclusion": sv.verification_conclusion,
                    "confidence_score": sv.confidence_score,
                    "supporting_evidence_count": len(sv.supporting_evidence),
                    "contradicting_evidence_count": len(sv.contradicting_evidence),
                }
                for sv in verification.statement_verifications
            ],
        }
        for hypothesis_id, verification in verification_results.items()
    }

    best_verified_hypothesis_id = max(
        verification_results.keys(),
        key=lambda k: verification_results[k].verification_score,
    )
    best_hypothesis_index = int(best_verified_hypothesis_id.split("_")[1])

    if best_hypothesis_index >= len(best_hypotheses):
        logger.warning(
            f"Best verified hypothesis index {best_hypothesis_index} is out of range, using first hypothesis"
        )
        best_hypothesis_index = 0

    # Create and return the final hypothesis
    return Hypothesis(
        title=best_hypotheses[best_hypothesis_index][0].title,
        statement=best_hypotheses[best_hypothesis_index][0].statement,
        source=subgraph,
        method=HypothesisGenerator(config),
        metadata={
            "verification_results": verification_metadata,
            "best_verified_hypothesis": best_verified_hypothesis_id,
            "score": best_hypotheses[best_hypothesis_index][2],
        },
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
