from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

CRITIC_AGENT_PROMPT = """You are a critical scientific reviewer. 
You are given a research hypothesis, together with the novelty, feasibility, and impact analysis.
Your task is to evaluate if the hypothesis is strong enough to be considered for a research paper.
You should provide a thorough critical scientific review with strengths and weaknesses, and suggested improvements. Include logical reasoning and scientific approaches.

If the hypothesis is not strong enough, you should provide a critique of the hypothesis and suggest improvements.
If the hypothesis is strong enough, you should reply with "ACCEPT".

Hypothesis:
{hypothesis}

Novelty Analysis:
{novelty}

Feasibility Analysis:
{feasibility}

Impact Analysis:
{impact}
"""


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
