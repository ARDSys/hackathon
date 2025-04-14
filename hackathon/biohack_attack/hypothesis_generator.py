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

# Define maximum characters based on ~4 chars/token for 128k tokens
# NOTE: This is an approximation. Actual token count depends on the specific tokenizer.
MAX_PROMPT_CHARS = 115000 * 4  # 512,000 characters


def truncate_prompt(prompt: str, max_chars: int = MAX_PROMPT_CHARS) -> str:
    """
    Truncates the prompt string if it exceeds the maximum character limit.

    Args:
        prompt: The input prompt string.
        max_chars: The maximum allowed characters.

    Returns:
        The potentially truncated prompt string.
    """
    if len(prompt) > max_chars:
        original_len = len(prompt)
        truncated_prompt = prompt[:max_chars]
        logger.warning(
            f"Input prompt length ({original_len} chars) exceeded limit ({max_chars} chars). "
            f"Truncating input."
        )
        return truncated_prompt
    return prompt


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
    # --- Input Check ---
    truncated_prompt = truncate_prompt(prompt)
    # -------------------

    result = await Runner.run(hypothesis_agent, input=truncated_prompt)
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
    # --- Input Check ---
    truncated_prompt = truncate_prompt(prompt)
    # -------------------

    triage_result = await Runner.run(rheumatology_triage_agent, input=truncated_prompt)
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
    # --- Input Check ---
    truncated_prompt = truncate_prompt(prompt)
    # -------------------

    result = await Runner.run(hypothesis_decomposer_agent, input=truncated_prompt)
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
    # --- Input Check ---
    truncated_prompt = truncate_prompt(prompt)
    # -------------------

    result = await Runner.run(statement_verification_agent, input=truncated_prompt)
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
    total_score = 0.0  # Initialize as float

    # Get all attributes of the triage object
    for attr_name in dir(triage):
        # Skip private/special attributes and methods
        if attr_name.startswith("_") or callable(getattr(triage, attr_name)):
            continue

        # Check if the attribute name contains 'assessment'
        if "assessment" in attr_name.lower():
            assessment = getattr(triage, attr_name)

            # Check if the assessment has score and confidence attributes and they are numeric
            if (
                hasattr(assessment, "score")
                and hasattr(assessment, "confidence")
                and isinstance(assessment.score, (int, float))
                and isinstance(assessment.confidence, (int, float))
            ):
                total_score += float(assessment.score) * float(
                    assessment.confidence
                )  # Ensure float multiplication
            # Optional: Log if assessment structure is unexpected
            # else:
            #    logger.debug(f"Attribute '{attr_name}' has 'assessment' but lacks valid score/confidence fields.")

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
    completed_tasks = await asyncio.gather(
        *[task for task in verification_tasks.values()], return_exceptions=True
    )

    # Match results back to hypothesis IDs
    task_list = list(verification_tasks.items())
    for i, result_or_exc in enumerate(completed_tasks):
        hypothesis_id, _ = task_list[i]
        if isinstance(result_or_exc, Exception):
            logger.error(
                f"Error verifying hypothesis {hypothesis_id}: {str(result_or_exc)}"
            )
            # Optionally store the error or a default value
            # results[hypothesis_id] = None # Or some error indicator object
        elif (
            result_or_exc
        ):  # Ensure result is not None if gather returns None for some reason
            results[hypothesis_id] = result_or_exc
            logger.info(
                f"Verified hypothesis {hypothesis_id} with score {result_or_exc.verification_score}"
            )
        else:
            logger.warning(f"Verification task for {hypothesis_id} returned None.")

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
    # --- Input Check ---
    truncated_prompt = truncate_prompt(prompt)
    # -------------------

    refined_hypothesis_result = await Runner.run(
        rheumatology_refiner_agent, input=truncated_prompt
    )
    refined_hypothesis = refined_hypothesis_result.final_output

    # Now process this refined hypothesis through the standard pipeline
    # Note: run_triage_agent, decompose_hypothesis, verify_hypothesis_decomposition
    # already contain their own input checks.
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
    # ONTOLOGY ENRICHMENT TASK - MANDATORY EXTERNAL VALIDATION

## MANDATE
You are an expert rheumatology ontology coordinator. Your primary goal in this task is **NOT** just to analyze the provided subgraph, but to **actively enrich and validate it using external, current information obtained via mandatory handoffs to your specialized research agents.** You MUST NOT rely solely on the information present in the initial subgraph or your internal knowledge base for generating the enrichment output.

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
    # --- Input Check ---
    truncated_input = truncate_prompt(ontology_input)
    # -------------------

    ontology_result = await Runner.run(ontology_agent, input=truncated_input)
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
    # verify_statement already includes truncation logic
    statement_verification_tasks = [
        verify_statement(statement)
        for statement in decomposition.falsifiable_statements
    ]
    # Using return_exceptions=True to handle potential errors in individual verifications
    statement_verifications_results = await asyncio.gather(
        *statement_verification_tasks, return_exceptions=True
    )

    # Filter out exceptions and log them
    statement_verifications = []
    for i, result in enumerate(statement_verifications_results):
        if isinstance(result, Exception):
            logger.error(
                f"Error verifying statement {i} ('{decomposition.falsifiable_statements[i].statement}'): {result}"
            )
        elif result:  # Check if result is not None
            statement_verifications.append(result)
        else:
            logger.warning(
                f"Verification for statement {i} ('{decomposition.falsifiable_statements[i].statement}') returned None."
            )

    logger.info(
        f"Completed verification of {len(statement_verifications)} statements (out of {len(decomposition.falsifiable_statements)})."
    )

    # Synthesize the results into a comprehensive assessment
    # Handle case where no statements were successfully verified
    if not statement_verifications:
        logger.warning(
            f"No statements successfully verified for hypothesis: {decomposition.original_hypothesis}. Returning default/empty verification."
        )
        # Return a default/empty HypothesisVerification object
        return HypothesisVerification(
            statement_verifications=[],
            overall_assessment="Verification could not be completed as no component statements were successfully verified.",
            verification_score=0.0,  # Or some other indicator of failure/low confidence
        )

    prompt = f"""
    # HYPOTHESIS ASSESSMENT TASK

    Please synthesize the verification results for the following hypothesis:

    ## ORIGINAL HYPOTHESIS

    "{decomposition.original_hypothesis}"

    ## VERIFICATION RESULTS FOR COMPONENT STATEMENTS

    {[v.model_dump_json(indent=2) for v in statement_verifications]}

    Please provide a comprehensive assessment of the overall hypothesis based on these verification results.
    Calculate a verification score (0.0 to 1.0) and confidence (0.0 to 1.0).
    """
    # --- Input Check ---
    truncated_prompt = truncate_prompt(prompt)
    # -------------------

    assessment_result = await Runner.run(
        hypothesis_assessment_agent, input=truncated_prompt
    )

    # Ensure the final result includes the actual statement verifications
    final_verification = assessment_result.final_output
    if isinstance(final_verification, HypothesisVerification):
        final_verification.statement_verifications = statement_verifications
        final_verification.original_hypothesis = (
            decomposition.original_hypothesis
        )  # Ensure original hypothesis is set
    else:
        # Handle unexpected result type from agent
        logger.error(
            f"Hypothesis assessment agent returned unexpected type: {type(final_verification)}"
        )
        # Fallback to creating a verification object
        final_verification = HypothesisVerification(
            statement_verifications=[],
            overall_assessment="Assessment agent failed to return valid structure.",
            verification_score=0.0,
        )

    return final_verification


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
        best_hypothesis_id=None,  # Initialize best_hypothesis_id
    )

    # Step 1: Run Ontology Agent (includes input check)
    try:
        ontology: OntologyAgentOutput = await run_ontology_agent(subgraph_model)
        dto.ontology = ontology
        logger.info(
            f"Ontology generated: {dto.ontology.model_dump_json(indent=2)}"
        )  # Use shorter log
    except Exception as e:
        logger.error(f"Failed to run ontology agent: {e}")
        raise ValueError("Ontology generation failed, cannot proceed.") from e

    # Process through iterations
    for iteration in range(config.max_iterations):
        dto.current_iteration = iteration
        logger.info(f"Starting iteration {iteration + 1}/{config.max_iterations}")

        # Initialize the list for this iteration
        if len(dto.hypotheses) <= iteration:
            dto.hypotheses.append([])

        hypothesis_tasks = []
        # Step 2: Generate hypotheses
        if iteration == 0:
            # First iteration: generate from scratch (run_hypothesis_agent includes input check)
            logger.info("Generating initial hypotheses...")
            hypothesis_tasks = [
                run_hypothesis_agent(subgraph_model, dto.ontology)
                for _ in range(config.num_of_hypotheses)
            ]
        else:
            # Later iterations: refine best hypotheses (refine_hypothesis includes input check)
            logger.info(f"Refining hypotheses from iteration {iteration}...")

            if iteration == 0 or not dto.hypotheses[iteration - 1]:
                logger.warning(
                    f"No hypotheses from previous iteration {iteration} to refine. Skipping refinement."
                )
                continue  # Or potentially break, depending on desired logic

            prev_hypotheses = dto.hypotheses[iteration - 1]
            # Sort by score, handling None scores
            prev_hypotheses.sort(
                key=lambda x: x.score if x.score is not None else float("-inf"),
                reverse=True,
            )

            top_k_refine = min(config.top_k, len(prev_hypotheses))
            if top_k_refine == 0:
                logger.warning(
                    f"No valid hypotheses with scores found in iteration {iteration} to refine."
                )
                continue

            best_prev_hypotheses = prev_hypotheses[:top_k_refine]
            logger.info(f"Selected top {top_k_refine} hypotheses for refinement.")

            # Refine each hypothesis
            hypothesis_tasks = [
                refine_hypothesis(prev_hypothesis, dto.ontology, iteration)
                for prev_hypothesis in best_prev_hypotheses
            ]

        # Execute generation/refinement tasks
        task_results = await asyncio.gather(*hypothesis_tasks, return_exceptions=True)

        # Collect valid results and log errors
        initial_hypotheses = []  # Renamed to avoid confusion
        for result in task_results:
            if isinstance(result, Exception):
                logger.error(
                    f"Error generating/refining hypothesis in iteration {iteration + 1}: {result}"
                )
            elif isinstance(
                result, ProcessedHypothesis
            ):  # Refiner returns ProcessedHypothesis
                initial_hypotheses.append(result.base_hypothesis)
            elif isinstance(
                result, ScientificHypothesis
            ):  # Generator returns ScientificHypothesis
                initial_hypotheses.append(result)
            else:
                logger.warning(
                    f"Unexpected result type from hypothesis task: {type(result)}"
                )

        if not initial_hypotheses:
            logger.error(
                f"Failed to generate any valid hypotheses in iteration {iteration + 1}."
            )
            # Decide whether to continue to next iteration or stop
            if iteration == 0:
                raise ValueError("Failed to generate any initial hypotheses.")
            else:
                logger.warning(
                    "Skipping further processing for this iteration due to lack of hypotheses."
                )
                continue  # Move to next iteration

        logger.info(
            f"Generated/Refined {len(initial_hypotheses)} hypotheses for iteration {iteration + 1}."
        )

        # Step 3: Triage hypotheses concurrently (run_triage_agent includes input check)
        logger.info("Triaging hypotheses...")
        triage_tasks = [
            run_triage_agent(hypothesis) for hypothesis in initial_hypotheses
        ]

        triage_task_results = await asyncio.gather(
            *triage_tasks, return_exceptions=True
        )

        triage_results = []
        for i, result in enumerate(triage_task_results):
            if isinstance(result, Exception):
                logger.error(
                    f"Error triaging hypothesis '{initial_hypotheses[i].title}': {result}"
                )
            elif isinstance(result, tuple) and len(result) == 2:
                triage_results.append(result)
            else:
                logger.warning(
                    f"Unexpected result type from triage task for '{initial_hypotheses[i].title}': {type(result)}"
                )

        logger.info(f"Triage completed for {len(triage_results)} hypotheses.")
        if not triage_results:
            logger.warning(
                f"No hypotheses successfully triaged in iteration {iteration + 1}. Skipping further processing."
            )
            continue

        # Step 4: Score hypotheses
        logger.info("Scoring hypotheses...")
        scored_hypotheses = []
        for hypothesis, triage in triage_results:
            try:
                score = score_hypothesis(triage)
                scored_hypotheses.append((hypothesis, triage, score))
            except Exception as e:
                logger.error(f"Error scoring hypothesis '{hypothesis.title}': {e}")
                # Assign a default low score or skip
                # scored_hypotheses.append((hypothesis, triage, float('-inf')))

        # Sort by score (descending), handling potential errors if scoring failed
        scored_hypotheses.sort(key=lambda x: x[2], reverse=True)

        # Update DTO with processed hypotheses for this iteration
        current_iter_hypotheses = []
        for i, (hypothesis, triage, score) in enumerate(scored_hypotheses):
            processed = ProcessedHypothesis(
                iteration=iteration,
                base_hypothesis=hypothesis,
                triaged_hypothesis=triage,
                score=score,
                # Initialize other fields to None, they'll be filled later
                decomposed_hypothesis=None,
                hypothesis_assessment=None,
            )
            current_iter_hypotheses.append(processed)
            logger.info(
                f"Iter {iteration+1} - Hypothesis {i}: '{hypothesis.title}', Triage score: {score:.4f}"
            )

        # Ensure the list for the current iteration exists before assigning
        if len(dto.hypotheses) <= iteration:
            dto.hypotheses.append([])
        dto.hypotheses[iteration] = (
            current_iter_hypotheses  # Assign the list for this iteration
        )

        # Select top k hypotheses for further processing (decomposition/verification)
        top_k_process = min(config.top_k, len(current_iter_hypotheses))
        if top_k_process == 0:
            logger.warning(
                f"No scored hypotheses to process further in iteration {iteration + 1}."
            )
            continue

        best_hypotheses_for_processing = current_iter_hypotheses[:top_k_process]
        logger.info(
            f"Selected top {top_k_process} hypotheses for decomposition and verification."
        )

        # Step 5: Decompose hypotheses concurrently (decompose_hypothesis includes input check)
        logger.info("Decomposing hypotheses...")
        decomposition_tasks = []
        decomposed_indices = (
            []
        )  # Store original index in best_hypotheses_for_processing

        for i, processed_hypothesis in enumerate(best_hypotheses_for_processing):
            decomposition_tasks.append(
                decompose_hypothesis(processed_hypothesis.base_hypothesis, dto.ontology)
            )
            decomposed_indices.append(i)

        decomposition_task_results = await asyncio.gather(
            *decomposition_tasks, return_exceptions=True
        )

        decomposition_results_map = {}  # Map index to decomposition result
        for i, result in enumerate(decomposition_task_results):
            original_index = decomposed_indices[i]
            hypothesis_title = best_hypotheses_for_processing[
                original_index
            ].base_hypothesis.title
            if isinstance(result, Exception):
                logger.error(
                    f"Error decomposing hypothesis '{hypothesis_title}': {result}"
                )
            elif isinstance(result, HypothesisDecomposition):
                decomposition_results_map[original_index] = result
            else:
                logger.warning(
                    f"Unexpected result type from decomposition task for '{hypothesis_title}': {type(result)}"
                )

        logger.info(
            f"Decomposition completed for {len(decomposition_results_map)} hypotheses."
        )
        if not decomposition_results_map:
            logger.warning(
                f"No hypotheses successfully decomposed in iteration {iteration + 1}. Skipping verification."
            )
            continue

        # Update DTO with decompositions
        successfully_decomposed_hypotheses = (
            []
        )  # List of (hypothesis_id, decomposition)
        for original_idx, decomposition in decomposition_results_map.items():
            # Update the ProcessedHypothesis object in the DTO directly
            if original_idx < len(dto.hypotheses[iteration]):
                dto.hypotheses[iteration][
                    original_idx
                ].decomposed_hypothesis = decomposition
                hypothesis_id = f"hypothesis_{original_idx}_{iteration}"  # Use original index from top_k list
                successfully_decomposed_hypotheses.append(
                    (hypothesis_id, decomposition)
                )
            else:
                logger.error(
                    f"Index mismatch when trying to update decomposition for index {original_idx}"
                )

        # Step 6: Verify decomposed hypotheses (verify_hypothesis_decomposition includes input check)
        logger.info("Verifying decomposed hypotheses...")
        if not successfully_decomposed_hypotheses:
            logger.warning("No successfully decomposed hypotheses to verify.")
            continue

        # verify_multiple_hypotheses handles parallelism internally
        verification_results = await verify_multiple_hypotheses(
            successfully_decomposed_hypotheses
        )
        logger.info(
            f"Verification completed for {len(verification_results)} hypotheses."
        )

        # Update DTO with verification results and find best verified in this iteration
        current_best_score = float("-inf")
        current_best_id = None
        for hypothesis_id, verification in verification_results.items():
            # Extract index and iteration from ID
            try:
                parts = hypothesis_id.split("_")
                idx = int(parts[1])
                iter_num = int(parts[2])

                if iter_num == iteration and idx < len(dto.hypotheses[iteration]):
                    # Update the ProcessedHypothesis object
                    dto.hypotheses[iteration][idx].hypothesis_assessment = verification

                    # Track best verified hypothesis *in this iteration*
                    if (
                        verification
                        and verification.verification_score > current_best_score
                    ):
                        current_best_score = verification.verification_score
                        current_best_id = hypothesis_id
                else:
                    logger.warning(
                        f"Mismatch or invalid index/iteration in hypothesis ID {hypothesis_id} for verification results."
                    )

            except (IndexError, ValueError) as e:
                logger.error(f"Could not parse hypothesis ID '{hypothesis_id}': {e}")

        if current_best_id:
            logger.info(
                f"Best verified hypothesis from iteration {iteration + 1}: {current_best_id} (Score: {current_best_score:.4f})"
            )
            # Update overall best if this iteration's best is better than previous overall best
            if (
                dto.best_hypothesis_id is None
                or current_best_score
                > dto.hypotheses[int(dto.best_hypothesis_id.split("_")[2])][
                    int(dto.best_hypothesis_id.split("_")[1])
                ].hypothesis_assessment.verification_score
            ):
                dto.best_hypothesis_id = current_best_id
                logger.info(
                    f"Updated overall best hypothesis ID to: {dto.best_hypothesis_id}"
                )
        else:
            logger.warning(
                f"No verified hypotheses found or scored in iteration {iteration + 1}"
            )

    # --- End of iterations ---

    # Identify the overall best hypothesis based on verification score
    final_best_processed_hypothesis = None
    best_score = float("-inf")
    best_iteration = -1
    best_index_in_iteration = -1  # Index within the dto.hypotheses[best_iteration] list

    if dto.best_hypothesis_id:
        try:
            parts = dto.best_hypothesis_id.split("_")
            best_index_in_iteration = int(parts[1])
            best_iteration = int(parts[2])

            if 0 <= best_iteration < len(
                dto.hypotheses
            ) and 0 <= best_index_in_iteration < len(dto.hypotheses[best_iteration]):
                candidate = dto.hypotheses[best_iteration][best_index_in_iteration]
                if candidate.hypothesis_assessment:
                    final_best_processed_hypothesis = candidate
                    best_score = candidate.hypothesis_assessment.verification_score
                    logger.info(
                        f"Selected best hypothesis based on verification ID: {dto.best_hypothesis_id} (Verification Score: {best_score:.4f})"
                    )
                else:
                    logger.warning(
                        f"Best hypothesis identified by ID {dto.best_hypothesis_id} lacks verification assessment."
                    )
            else:
                logger.error(
                    f"Best hypothesis ID {dto.best_hypothesis_id} points to invalid iteration/index."
                )
        except (IndexError, ValueError, TypeError) as e:
            logger.error(
                f"Error processing best_hypothesis_id '{dto.best_hypothesis_id}': {e}"
            )
            dto.best_hypothesis_id = None  # Reset if invalid

    # Fallback: If no verified best, find the highest *triaged* score across all iterations
    if final_best_processed_hypothesis is None:
        logger.warning(
            "Could not determine best hypothesis from verification scores. Falling back to highest triage score."
        )
        best_score = float("-inf")  # Reset best score for triage comparison
        for i, iteration_hypotheses in enumerate(dto.hypotheses):
            for j, hyp in enumerate(iteration_hypotheses):
                if hyp.score is not None and hyp.score > best_score:
                    best_score = hyp.score
                    final_best_processed_hypothesis = hyp
                    best_iteration = i
                    best_index_in_iteration = j
                    # Update best_hypothesis_id for consistency, even if based on triage score
                    dto.best_hypothesis_id = f"hypothesis_{j}_{i}"

    if final_best_processed_hypothesis is None:
        logger.error("Failed to identify any suitable hypothesis after all iterations.")
        raise ValueError("Failed to identify any valid hypotheses after processing.")

    logger.info(
        f"Final selected best hypothesis: ID {dto.best_hypothesis_id}, "
        f"Title: '{final_best_processed_hypothesis.base_hypothesis.title}', "
        f"Final Score (best of verification/triage): {best_score:.4f}"
    )

    # Save full DTO state if path provided
    if config.out_dir_path is not None:
        out_file = config.out_dir_path / "process_state.json"
        try:
            config.out_dir_path.mkdir(parents=True, exist_ok=True)
            with open(out_file, "wt") as f:
                f.write(dto.model_dump_json(indent=2))
            logger.info(f"Saved final process state to {out_file}")
        except Exception as e:
            logger.error(f"Failed to save process state to {out_file}: {e}")

    # Create verification metadata for the final report
    verification_metadata = {}
    for iter_idx, iteration_data in enumerate(dto.hypotheses):
        for hyp_idx, hyp in enumerate(iteration_data):
            if hyp.hypothesis_assessment:
                hypothesis_id = f"hypothesis_{hyp_idx}_{iter_idx}"
                assessment = hyp.hypothesis_assessment
                verif_meta = {
                    "verification_score": getattr(
                        assessment, "verification_score", None
                    ),
                    "overall_assessment": getattr(
                        assessment, "overall_assessment", "N/A"
                    ),
                    "statement_verifications": [],
                }
                if (
                    hasattr(assessment, "statement_verifications")
                    and assessment.statement_verifications
                ):
                    for sv in assessment.statement_verifications:
                        verif_meta["statement_verifications"].append(
                            {
                                "statement": getattr(sv, "statement", "N/A"),
                                "verification_conclusion": getattr(
                                    sv, "verification_conclusion", "N/A"
                                ),
                                "confidence_score": getattr(
                                    sv, "confidence_score", None
                                ),
                                "supporting_evidence_count": len(
                                    getattr(sv, "supporting_evidence", [])
                                ),
                                "contradicting_evidence_count": len(
                                    getattr(sv, "contradicting_evidence", [])
                                ),
                            }
                        )
                verification_metadata[hypothesis_id] = verif_meta

    # Ensure base hypothesis exists before accessing attributes
    base_hyp = final_best_processed_hypothesis.base_hypothesis
    if not base_hyp:
        raise ValueError(
            f"Final best ProcessedHypothesis (ID: {dto.best_hypothesis_id}) is missing its base_hypothesis."
        )

    # Create and return the final ARD Hypothesis object
    final_hypothesis = Hypothesis(
        title=base_hyp.title,
        statement=base_hyp.statement,
        source=subgraph,  # Original subgraph input
        method=HypothesisGenerator(config),  # Reference to this generator instance
        metadata={
            "final_selected_hypothesis_id": dto.best_hypothesis_id,
            "final_score": best_score,  # The score used for final selection (verification or triage)
            "best_hypothesis_iteration": best_iteration,
            "best_hypothesis_index_in_iteration": best_index_in_iteration,
            "total_iterations_run": dto.current_iteration
            + 1,  # iterations are 0-indexed
            "all_verification_results": verification_metadata,
            # Include triage score of the final hypothesis for reference
            "final_hypothesis_triage_score": final_best_processed_hypothesis.score,
        },
    )

    return final_hypothesis, dto


class HypothesisGenerator(HypothesisGeneratorProtocol):
    def __init__(self, config: Optional[ProcessConfig] = None):
        self.config = config or ProcessConfig()
        self.dto: Optional[HypothesisGenerationDTO] = (
            None  # Will store the DTO after running
        )
        self._loop = None  # Store event loop reference

    async def async_run(self, subgraph: Subgraph) -> Hypothesis:
        """Async version of run method"""
        # run_agents now returns hypothesis, dto
        hypothesis, self.dto = await run_agents(subgraph, self.config)
        return hypothesis

    def run(self, subgraph: Subgraph) -> Hypothesis:
        """Synchronous entry point that manages the event loop"""
        try:
            # Get existing loop if available (e.g., running in Jupyter)
            loop = asyncio.get_running_loop()
            logger.info("Using existing event loop.")
            # If using an existing loop, ensure it's managed externally
            is_external_loop = True
        except RuntimeError:
            # No running loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("Created new event loop.")
            is_external_loop = False
            self._loop = loop  # Store only if we created it

        try:
            # Run the async function and wait for completion
            hypothesis = loop.run_until_complete(self.async_run(subgraph))
            return hypothesis
        finally:
            # Only close the loop if this function created it
            if not is_external_loop and self._loop:
                self._loop.close()
                asyncio.set_event_loop(None)  # Clean up loop association
                logger.info("Closed event loop.")
                self._loop = None

    def get_state(self) -> Optional[HypothesisGenerationDTO]:
        """Return the final state DTO of the hypothesis generation process."""
        if self.dto is None:
            logger.warning("get_state() called before run() completed or run() failed.")
        return self.dto

    def __str__(self) -> str:
        # Provide more config details in the string representation
        return (
            f"HypothesisGenerator(iterations={self.config.max_iterations}, "
            f"hypotheses_per_iter={self.config.num_of_hypotheses}, "
            f"top_k={self.config.top_k})"
        )

    def to_json(self) -> dict[str, Any]:
        # Include config in the JSON representation
        return {
            "type": "HypothesisGenerator",
            "config": self.config.__dict__ if self.config else None,
        }
