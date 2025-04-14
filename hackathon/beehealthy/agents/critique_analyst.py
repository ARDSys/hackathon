from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

CRITIC_AGENT_PROMPT = """
You are the CRITIC ANALYST in a collaborative multi-agent system for generating and validating research hypotheses in medical science.

You are provided with a hypothesis along with evaluations from specialized agents in the areas of:
- Novelty
- Feasibility
- Potential Impact

Your task is to conduct a critical, structured review of the hypothesis using scientific reasoning and domain knowledge. Your evaluation should include:

1. **Overall Strength of the Hypothesis**: Assess clarity, originality, and relevance to the medical domain.
2. **Scientific Strengths**: Identify robust or innovative aspects supported by the evaluations.
3. **Weaknesses or Concerns**: Highlight scientific, ethical, feasibility, or impact-related limitations.
4. **Suggested Improvements**: Recommend specific ways to strengthen the hypothesis or adjust methodology.
5. **Final Decision**: Reply with:
   - `"ACCEPT"` if the hypothesis is scientifically sound and ready for experimental planning.
   - `"REVISE"` if improvements are needed before proceeding.
   - `"REJECT"` if the hypothesis is fundamentally flawed.

Use precise scientific language and structure your reasoning clearly. Your response will guide downstream agents in refining, testing, or summarizing the hypothesis.
---

Hypothesis:
{hypothesis}

Novelty Analysis:
{novelty}

Feasibility Analysis:
{feasibility}

Impact Analysis:
{impact}
"""

# Ethics and Bias Analysis:
# {ethics_analysis}


def create_critique_analyst_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a critique analyst agent that evaluates the overall research proposal."""

    prompt = PromptTemplate.from_template(CRITIC_AGENT_PROMPT)

    # Use provided model or get default large model
    model = get_model(model, **kwargs)

    chain = prompt | model

    def agent(state: HypgenState) -> HypgenState:
        """Evaluate the overall research proposal and provide critique."""
        logger.info("Starting critique analysis")
        # Run the chain
        response = chain.invoke(state)

        logger.info("Critique analysis completed successfully")
        return {
            "critique": response.content,
            "messages": [add_role(response, "critique_analyst")],
        }

    return {"agent": agent}
