from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

REVIEW_AGENT_PROMPT = """You are a balanced scientific reviewer tasked with evaluating a research hypothesis.
You have been provided with both supporting arguments (from a devil's advocate) and critical arguments (from a critique).
Your task is to weigh these arguments and provide a final numerical evaluation.

Scoring criteria (0.0 to 1.0):
- 0.0: Hypothesis is fundamentally flawed or impractical
- 0.25: Significant concerns outweigh potential benefits
- 0.5: Equal balance of strengths and limitations
- 0.75: Strong potential with manageable limitations
- 1.0: Exceptional hypothesis with minimal concerns

Supporting Arguments:
{pros_analysis}

Critical Arguments:
{cons_analysis}

Hypothesis:
{hypothesis}

Your response must be structured exactly as follows:

BALANCED ANALYSIS:
[Your detailed analysis explaining the score, considering both supporting and critical arguments]

SCORE: [numerical_score]
"""

def create_review_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a review agent that evaluates arguments for and against the hypothesis."""

    prompt = PromptTemplate.from_template(REVIEW_AGENT_PROMPT)
    model = get_model(model, **kwargs)
    chain = prompt | model

    def agent(state: HypgenState) -> HypgenState:
        """Evaluate the hypothesis based on pros and cons analysis."""
        logger.info("Starting review analysis")
        
        response = chain.invoke({
            **state,
            "hypothesis": state["hypothesis"],
            "pros_analysis": state["pros_analysis"],
            "cons_analysis": state["cons_analysis"]
        })
        
        # Extract numerical score from response
        score_line = response.content.split("\n")[-1]
        try:
            score = float(score_line.replace("SCORE:", "").strip())
        except (ValueError, IndexError):
            logger.warning("Could not parse score from response, defaulting to 0.5")
            score = 0.5
        
        logger.info(f"Review completed with score: {score}")
        
        return {
            "review": response.content,
            "score": score,
            "messages": [add_role(response, "review")]
        }

    return {"agent": agent}