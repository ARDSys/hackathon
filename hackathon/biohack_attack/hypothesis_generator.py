import asyncio
from dataclasses import dataclass
from pathlib import Path
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
    FalsifiableStatement,
)
from biohack_attack.hackathon_agents.hypothesis_agent import (
    hypothesis_agent,
    ScientificHypothesis,
)
from biohack_attack.hackathon_agents.hypothesis_assigment_agent import (
    hypothesis_assessment_agent,
)
from biohack_attack.hackathon_agents.ontology_agent import (
    ontology_agent,
    OntologyAgentOutput,
)
from biohack_attack.hackathon_agents.refiner_agent import rheumatology_refiner_agent
from biohack_attack.hackathon_agents.verification_agent import (
    HypothesisVerification,
    statement_verification_agent,
    StatementVerification,
)
from biohack_attack.model import SubgraphModel


@dataclass
class ProcessConfig:
    num_of_hypotheses: int = 5
    num_of_threads: int = 5
    top_k: int = 2
    max_iterations: int = 2
    out_dir_path: Optional[Path] = None


async def run_hypothesis_agent(
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
    # Changed from asyncio.run to directly awaiting
    result = await Runner.run(hypothesis_agent, input=prompt)
    return result.final_output


async def run_triage_agent(
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
    triage_result = await Runner.run(rheumatology_triage_agent, input=prompt)
    return hypothesis, triage_result.final_output


async def decompose_hypothesis(
    hypothesis: ScientificHypothesis, ontology: OntologyAgentOutput
) -> HypothesisDecomposition:
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


# Modified to properly handle async in threads
async def run_in_executor(executor, func, *args):
    """Run a synchronous function in a thread pool executor."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, func, *args)


async def verify_statement(statement: FalsifiableStatement) -> StatementVerification:
    """
    Verify a falsifiable statement using the verification agent.

    Args:
        statement: The FalsifiableStatement to verify

    Returns:
        A StatementVerification containing the verification results
    """
    prompt = f"""
    # STATEMENT VERIFICATION TASK

    Please verify the following scientific statement by searching for supporting and contradicting evidence:

    ## STATEMENT TO VERIFY

    "{statement.statement}"

    ## PROPOSED FALSIFICATION METHOD

    {statement.falsification_method}

    ## EXISTING SUPPORTING EVIDENCE (IF ANY)

    {statement.supporting_evidence if statement.supporting_evidence else "None provided"}

    ## EXISTING CONTRADICTING EVIDENCE (IF ANY)

    {statement.contradicting_evidence if statement.contradicting_evidence else "None provided"}

    Please conduct a thorough search using the available tools to find both supporting and contradicting evidence.
    Then provide a comprehensive verification assessment.
    """

    result = await Runner.run(statement_verification_agent, input=prompt)
    return result.final_output


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

    refined_hypothesis_result = await Runner.run(
        rheumatology_refiner_agent, input=prompt
    )
    refined_hypothesis = refined_hypothesis_result.final_output

    # Now process this refined hypothesis through the standard pipeline
    base_hypothesis, triage = await run_triage_agent(refined_hypothesis)
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


async def verify_hypothesis_decomposition(
    decomposition: HypothesisDecomposition,
) -> HypothesisVerification:
    """
    Verify a decomposed hypothesis by verifying each of its falsifiable statements and
    then synthesizing the results.

    Args:
        decomposition: The HypothesisDecomposition to verify

    Returns:
        A HypothesisVerification containing the verification results
    """
    logger.info(
        f"Starting verification of hypothesis: {decomposition.original_hypothesis}"
    )

    # Verify all statements in parallel
    statement_verification_tasks = [
        verify_statement(statement)
        for statement in decomposition.falsifiable_statements
    ]
    statement_verifications = await asyncio.gather(*statement_verification_tasks)

    logger.info(f"Completed verification of {len(statement_verifications)} statements")

    # Synthesize the results into a comprehensive assessment
    prompt = f"""
    # HYPOTHESIS ASSESSMENT TASK

    Please synthesize the verification results for the following hypothesis:

    ## ORIGINAL HYPOTHESIS

    "{decomposition.original_hypothesis}"

    ## VERIFICATION RESULTS FOR COMPONENT STATEMENTS

    {[v.model_dump_json(indent=2) for v in statement_verifications]}

    Please provide a comprehensive assessment of the overall hypothesis based on these verification results.
    """

    assessment_result = await Runner.run(hypothesis_assessment_agent, input=prompt)
    return assessment_result.final_output


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

    ontology: OntologyAgentOutput = await run_ontology_agent(subgraph_model)
    dto.ontology = ontology
    logger.info(dto.ontology.model_dump_json(indent=4))

    # Process through iterations
    for iteration in range(config.max_iterations):
        dto.current_iteration = iteration
        logger.info(f"Starting iteration {iteration + 1}/{config.max_iterations}")

        # Initialize the list for this iteration
        dto.hypotheses.append([])

        # Step 2: Generate hypotheses using parallel coroutines
        if iteration == 0:
            # First iteration: generate from scratch
            logger.info("Generating initial hypotheses...")
            hypothesis_tasks = [
                run_hypothesis_agent(subgraph_model, dto.ontology)
                for _ in range(config.num_of_hypotheses)
            ]

            hypothesis_results = []
            for task in asyncio.as_completed(hypothesis_tasks):
                try:
                    hypothesis = await task
                    hypothesis_results.append(hypothesis)
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
            refine_tasks = [
                refine_hypothesis(prev_hypothesis, dto.ontology, iteration)
                for prev_hypothesis in best_prev_hypotheses
            ]

            hypothesis_results = []
            for task in asyncio.as_completed(refine_tasks):
                try:
                    refined = await task
                    hypothesis_results.append(refined.base_hypothesis)
                except Exception as e:
                    logger.error(f"Error refining hypothesis: {str(e)}")

        if not hypothesis_results:
            raise ValueError("Failed to generate any valid hypotheses")

        logger.info(
            f"Generated {len(hypothesis_results)} hypotheses for iteration {iteration + 1}."
        )

        # Step 3: Triage hypotheses concurrently
        logger.info("Triaging hypotheses...")
        triage_tasks = [
            run_triage_agent(hypothesis) for hypothesis in hypothesis_results
        ]

        triage_results = []
        for task in asyncio.as_completed(triage_tasks):
            try:
                triage_result = await task
                triage_results.append(triage_result)
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
            logger.info(f"Hypothesis {i}: {hypothesis.title}, Total score: {score}")

        # Select top k hypotheses for further processing
        top_k = min(config.top_k, len(scored_hypotheses))
        best_hypotheses = scored_hypotheses[:top_k]

        logger.info(f"Selected top {top_k} hypotheses for further processing.")

        # Step 5: Decompose hypotheses concurrently
        logger.info("Decomposing hypotheses...")
        decomposition_tasks = []
        decomposed_indices = []

        for i, (hypothesis, _, _) in enumerate(best_hypotheses):
            decomposition_tasks.append(decompose_hypothesis(hypothesis, dto.ontology))
            decomposed_indices.append(i)

        decomposition_results = []
        for i, task in enumerate(asyncio.as_completed(decomposition_tasks)):
            try:
                decomposition = await task
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

    if config.out_dir_path is not None:
        with open("process.json", "wt") as f:
            f.write(dto.model_dump_json(indent=4))

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
        self._loop = None  # Store event loop reference

    async def async_run(self, subgraph: Subgraph) -> Hypothesis:
        """Async version of run method"""
        hypothesis, self.dto = await run_agents(subgraph, self.config)
        return hypothesis

    def run(self, subgraph: Subgraph) -> Hypothesis:
        """Synchronous entry point that creates a new event loop"""
        # Create new event loop if running in synchronous context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop

        try:
            hypothesis = loop.run_until_complete(self.async_run(subgraph))
            return hypothesis
        finally:
            loop.close()
            self._loop = None

    def get_state(self) -> Optional[HypothesisGenerationDTO]:
        """Return the current state of the hypothesis generation process."""
        return self.dto

    def __str__(self) -> str:
        return "HypeGen Generator"

    def to_json(self) -> dict[str, Any]:
        return {"type": "HypothesisGenerator"}
