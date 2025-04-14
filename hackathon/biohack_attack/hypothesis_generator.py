import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Optional, List, Tuple, Dict

from agents import Runner
from loguru import logger

from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph
from biohack_attack.dto import ProcessedHypothesis, HypothesisGenerationDTO
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
from biohack_attack.hackathon_agents.refiner_agent import rheumatology_refiner_agent
from biohack_attack.hackathon_agents.verification_agent import HypothesisVerification
from biohack_attack.model import SubgraphModel


@dataclass
class ProcessConfig:
    num_of_hypotheses: int = 5
    num_of_threads: int = 5
    top_k: int = 2
    max_iterations: int = 2


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


async def refine_hypothesis(
    hypothesis: ProcessedHypothesis, ontology: OntologyAgentOutput, iteration: int
) -> ProcessedHypothesis:
    """
    Refine a hypothesis based on previous assessment.

    Args:
        hypothesis: The processed hypothesis to refine
        ontology: Ontology information to enrich understanding
        iteration: Current iteration number

    Returns:
        A new ProcessedHypothesis with refined information
    """
    # Add refinement logic here when needed
    # For now, we just create a new hypothesis
    prompt = f"""
    # HYPOTHESIS REFINEMENT TASK

    Please refine the following scientific hypothesis based on the assessment:

    ## ORIGINAL HYPOTHESIS
    Title: {hypothesis.base_hypothesis.title}
    Statement: {hypothesis.base_hypothesis.statement}
    Mechanism: {hypothesis.base_hypothesis.mechanism.pathway_description if hypothesis.base_hypothesis.mechanism else "Not specified"}

    ## ASSESSMENT FEEDBACK
    {hypothesis.hypothesis_assessment.overall_assessment if hypothesis.hypothesis_assessment else "Not available"}

    ## VERIFICATION DETAILS
    {[v.verification_conclusion for v in hypothesis.hypothesis_assessment.statement_verifications] if hypothesis.hypothesis_assessment else "Not available"}

    ## ONTOLOGY ENRICHMENT
    The following additional ontological information has been provided to enrich your understanding:
    <ontology>
    {ontology.model_dump_json(indent=2)}
    </ontology>

    Please generate an improved version of this hypothesis that addresses the identified issues.
    """

    refined_hypothesis = asyncio.run(
        Runner.run(rheumatology_refiner_agent, input=prompt)
    ).final_output

    # Now process this refined hypothesis through the standard pipeline
    _, triage = run_triage_agent(refined_hypothesis)
    score = score_hypothesis(triage)

    decomposed = await decompose_hypothesis(refined_hypothesis, ontology)

    verification_result = await verify_hypothesis_decomposition(decomposed)

    return ProcessedHypothesis(
        iteration=iteration,
        base_hypothesis=refined_hypothesis,
        triaged_hypothesis=triage,
        decomposed_hypothesis=decomposed,
        hypothesis_assessment=verification_result,
        score=score,
    )


async def run_agents(
    subgraph: Subgraph, config: ProcessConfig
) -> Tuple[Hypothesis, HypothesisGenerationDTO]:
    # Convert the subgraph to a model
    subgraph_model = SubgraphModel.from_subgraph(subgraph)

    # Initialize our DTO to maintain state
    dto = HypothesisGenerationDTO(
        subgraph_model=subgraph_model,
        ontology=None,  # Will be populated in step 1
        hypotheses=[],
        current_iteration=0,
    )

    # Step 1: Enrich subgraph with ontology agent
    logger.info("Enriching subgraph with ontology agent...")
    dto.ontology = await run_ontology_agent(subgraph_model)
    logger.debug(dto.ontology.model_dump_json(indent=4))

    # Process through iterations
    for iteration in range(config.max_iterations):
        dto.current_iteration = iteration
        logger.info(f"Starting iteration {iteration + 1}/{config.max_iterations}")

        # Initialize the list for this iteration
        dto.hypotheses.append([])

        # Step 2: Generate hypotheses using ThreadPoolExecutor
        if iteration == 0:
            # First iteration: generate from scratch
            logger.info("Generating initial hypotheses...")
            hypothesis_results = []
            with ThreadPoolExecutor(max_workers=config.num_of_threads) as executor:
                futures = [
                    executor.submit(run_hypothesis_agent, subgraph_model, dto.ontology)
                    for _ in range(config.num_of_hypotheses)
                ]
                for future in futures:
                    try:
                        hypothesis_results.append(future.result())
                    except Exception as e:
                        logger.error(f"Error generating hypothesis: {str(e)}")
        else:
            # Later iterations: refine best hypotheses from previous iteration
            logger.info(f"Refining hypotheses from iteration {iteration}...")

            # Get top hypotheses from previous iteration
            prev_hypotheses = dto.hypotheses[iteration - 1]
            prev_hypotheses.sort(
                key=lambda x: x.score if x.score is not None else 0, reverse=True
            )

            # Take top_k hypotheses for refinement
            top_k = min(config.top_k, len(prev_hypotheses))
            best_prev_hypotheses = prev_hypotheses[:top_k]

            # Refine each hypothesis
            hypothesis_results = []
            for prev_hypothesis in best_prev_hypotheses:
                try:
                    refined = await refine_hypothesis(
                        prev_hypothesis, dto.ontology, iteration
                    )
                    hypothesis_results.append(refined.base_hypothesis)
                except Exception as e:
                    logger.error(f"Error refining hypothesis: {str(e)}")

        if not hypothesis_results:
            raise ValueError("Failed to generate any valid hypotheses")

        logger.info(
            f"Generated {len(hypothesis_results)} hypotheses for iteration {iteration + 1}."
        )

        # Step 3: Triage hypotheses using ThreadPoolExecutor
        logger.info("Triaging hypotheses...")
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

        logger.info(f"Triage completed for {len(triage_results)} hypotheses.")

        logger.info("Scoring hypotheses...")
        scored_hypotheses = [
            (hypothesis, triage, score_hypothesis(triage))
            for hypothesis, triage in triage_results
        ]
        scored_hypotheses.sort(key=lambda x: x[2], reverse=True)

        # Update DTO with processed hypotheses
        for i, (hypothesis, triage, score) in enumerate(scored_hypotheses):
            processed = ProcessedHypothesis(
                iteration=iteration,
                base_hypothesis=hypothesis,
                triaged_hypothesis=triage,
                score=score,
            )
            dto.hypotheses[iteration].append(processed)
            logger.debug(f"Hypothesis {i}: {hypothesis.title}, Total score: {score}")

        # Select top k hypotheses for further processing
        top_k = min(config.top_k, len(scored_hypotheses))
        best_hypotheses = scored_hypotheses[:top_k]

        logger.info(f"Selected top {top_k} hypotheses for further processing.")

        # Step 5: Decompose hypotheses using ThreadPoolExecutor with wrapper function
        logger.info("Decomposing hypotheses...")
        decomposition_results = []
        decomposed_indices = []
        with ThreadPoolExecutor(max_workers=config.num_of_threads) as executor:
            futures = []
            for i, (hypothesis, _, _) in enumerate(best_hypotheses):
                futures.append(
                    executor.submit(
                        decompose_hypothesis_wrapper, hypothesis, dto.ontology
                    )
                )
                decomposed_indices.append(i)

            # Collect results, handle any exceptions
            for i, future in enumerate(futures):
                try:
                    decomposition = future.result()
                    decomposition_results.append((decomposed_indices[i], decomposition))
                except Exception as e:
                    logger.error(f"Error decomposing hypothesis: {str(e)}")

        logger.info(
            f"Decomposition completed for {len(decomposition_results)} hypotheses."
        )

        # Update DTO with decompositions
        for idx, decomposition in decomposition_results:
            if idx < len(dto.hypotheses[iteration]):
                dto.hypotheses[iteration][idx].decomposed_hypothesis = decomposition

        # Step 6: Verify decomposed hypotheses
        logger.info("Verifying decomposed hypotheses...")
        hypothesis_decompositions = [
            (f"hypothesis_{i}_{iteration}", decomp)
            for i, decomp in [(idx, result) for idx, result in decomposition_results]
        ]

        verification_results = await verify_multiple_hypotheses(
            hypothesis_decompositions
        )
        logger.info(
            f"Verification completed for {len(verification_results)} hypotheses."
        )

        # Update DTO with verification results
        for hypothesis_id, verification in verification_results.items():
            parts = hypothesis_id.split("_")
            if len(parts) >= 2:
                idx = int(parts[1])
                if idx < len(dto.hypotheses[iteration]):
                    dto.hypotheses[iteration][idx].hypothesis_assessment = verification

        # Find best verified hypothesis
        if verification_results:
            best_verified_hypothesis_id = max(
                verification_results.keys(),
                key=lambda k: verification_results[k].verification_score,
            )
            dto.best_hypothesis_id = best_verified_hypothesis_id

            # For analysis purpose in the log
            parts = best_verified_hypothesis_id.split("_")
            if len(parts) >= 2:
                best_hypothesis_index = int(parts[1])
                logger.info(
                    f"Best verified hypothesis from iteration {iteration + 1}: {best_hypothesis_index}"
                )
        else:
            logger.warning("No verified hypotheses in this iteration")

    # End of iterations - construct final hypothesis to return
    # Find the overall best hypothesis across all iterations
    best_hypothesis = None
    best_score = -1
    best_iteration = -1
    best_index = -1

    if dto.best_hypothesis_id:
        parts = dto.best_hypothesis_id.split("_")
        if len(parts) >= 3:
            best_index = int(parts[1])
            best_iteration = int(parts[2])

            if 0 <= best_iteration < len(dto.hypotheses) and 0 <= best_index < len(
                dto.hypotheses[best_iteration]
            ):
                best_hypothesis = dto.hypotheses[best_iteration][best_index]
                best_score = (
                    best_hypothesis.score if best_hypothesis.score is not None else 0
                )

    # If no best hypothesis was found, just take the best from the last iteration
    if best_hypothesis is None and dto.hypotheses:
        last_iteration = dto.hypotheses[-1]
        if last_iteration:
            # Sort by score
            last_iteration.sort(
                key=lambda x: x.score if x.score is not None else 0, reverse=True
            )
            best_hypothesis = last_iteration[0]
            best_score = (
                best_hypothesis.score if best_hypothesis.score is not None else 0
            )
            best_iteration = len(dto.hypotheses) - 1
            best_index = 0

    if best_hypothesis is None:
        raise ValueError("Failed to identify any valid hypotheses")

    # Create verification metadata
    verification_metadata = {}
    for iter_idx, iteration in enumerate(dto.hypotheses):
        for hyp_idx, hyp in enumerate(iteration):
            if hyp.hypothesis_assessment:
                hypothesis_id = f"hypothesis_{hyp_idx}_{iter_idx}"
                verification_metadata[hypothesis_id] = {
                    "verification_score": hyp.hypothesis_assessment.verification_score,
                    "overall_assessment": hyp.hypothesis_assessment.overall_assessment,
                    "statement_verifications": [
                        {
                            "statement": sv.statement,
                            "verification_conclusion": sv.verification_conclusion,
                            "confidence_score": sv.confidence_score,
                            "supporting_evidence_count": len(sv.supporting_evidence),
                            "contradicting_evidence_count": len(
                                sv.contradicting_evidence
                            ),
                        }
                        for sv in hyp.hypothesis_assessment.statement_verifications
                    ],
                }

    # Create and return the final hypothesis with complete metadata
    return (
        Hypothesis(
            title=best_hypothesis.base_hypothesis.title,
            statement=best_hypothesis.base_hypothesis.statement,
            source=subgraph,
            method=HypothesisGenerator(config),
            metadata={
                "verification_results": verification_metadata,
                "best_verified_hypothesis": dto.best_hypothesis_id,
                "score": best_score,
                "total_iterations": config.max_iterations,
                "best_iteration": best_iteration,
                "best_hypothesis_index": best_index,
            },
        ),
        dto,
    )


class HypothesisGenerator(HypothesisGeneratorProtocol):
    def __init__(self, config: Optional[ProcessConfig] = None):
        self.config = config or ProcessConfig()
        self.dto = None  # Will store the DTO after running

    def run(self, subgraph: Subgraph) -> Hypothesis:
        hypothesis, self.dto = asyncio.run(run_agents(subgraph, self.config))
        return hypothesis

    def get_state(self) -> Optional[HypothesisGenerationDTO]:
        """Return the current state of the hypothesis generation process."""
        return self.dto

    def __str__(self) -> str:
        return "HypeGen Generator"

    def to_json(self) -> dict[str, Any]:
        return {"type": "HypothesisGenerator"}
