from typing import Any, Dict, List, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger
from pydantic import BaseModel, Field

from ..llm.utils import get_model
from ..state import HypgenState

# Summary prompt
SUMMARY_PROMPT = """You are a skilled scientific writer contributing to a multi-agent research system.

Your task is to synthesize a clear, well-structured summary of a proposed scientific hypothesis, along with an analysis of its novelty, feasibility, and impact. The summary should be concise but informative, suitable for inclusion in a scientific report or research proposal.

Follow the exact structure below:

### Hypothesis
Provide a brief but precise restatement of the hypothesis, highlighting its core idea and research intention.

### Novelty Assessment: Not novel / Somewhat novel / Novel / Very novel
Summarize the novelty evaluation. Mention the key reasons the hypothesis is considered (or not considered) novel, based on existing literature and conceptual uniqueness.

### Feasibility Assessment: Not feasible / Somewhat feasible / Feasible
Summarize the feasibility analysis. Consider practical implementation, methodological soundness, availability of data or tools, and alignment with current research capabilities.

### Impact Assessment: Not impactful / Somewhat impactful / Impactful / Very impactful
Summarize the potential scientific or clinical impact. Address possible contributions to knowledge, patient outcomes, public health, or future research directions.

### References
Include the provided references that support the assessment of this hypothesis. These are crucial for validating the novelty, feasibility, and impact claims.

Important:
- Use scientific, objective language.
- Do not add interpretations or opinions not present in the input analysis.
- Avoid unnecessary repetition of the same phrases across sections.

Input:
Hypothesis:
{hypothesis}

Methodology review and analysis:
{methodology_review_summary_output}

References:
{references}
"""


class HypothesisSummary(BaseModel):
    title: str = Field(description="A concise title for the hypothesis")
    summary: str = Field(
        description="A detailed summary of the hypothesis and its assessment"
    )
    references: List[str] = Field(
        default_factory=list, description="References used in the hypothesis evaluation"
    )


def create_summary_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a summary agent that synthesizes the hypothesis evaluation results."""

    prompt = PromptTemplate.from_template(SUMMARY_PROMPT)

    llm = get_model(model, **kwargs).with_structured_output(HypothesisSummary)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the hypothesis and the analysis and return a summary."""
        logger.info("Starting summary generation")

        # Get references from the state
        references = state.get("references", [])
        reference_text = (
            "\n".join(references) if references else "No references provided."
        )

        # Add references to the state for the prompt
        state_with_refs = {**state, "references": reference_text}

        # Run the chain
        response = chain.invoke(state_with_refs)

        logger.info("Summary generated successfully")
        return {
            "summary": response.summary,
            "title": response.title,
            "references": references,  # Include the references in the final output
        }

    return {"agent": agent}
