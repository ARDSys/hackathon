from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

ANALYST_PROMPT = """
You are a critical AI assistant collaborating with a group of scientists to assess the {analysis_type} of a research proposal. 

Your primary task is to evaluate a proposed research hypothesis for its {task}

After careful analysis, return your estimations for the {analysis_type} as one of the following:
- "No {analysis_type}"
- "Some {analysis_type}"
- "High {analysis_type}"

Provide your reasoning for your assessment.
Cite the literature to support your assessment.

Literature information gathered by the research assistant:
{literature}

Hypothesis:
{hypothesis}
"""

# "Your primary task is to evaluate a proposed research hypothesis for its ..."
PROMPT_TASK_TEMPLATES = {
    "novelty": """
    novelty ensuring it does not overlap significantly with existing literature or delve into areas that are already well-explored.
    """,
    "feasibility": """
    feasibility considering the resources, time, and technical challenges.
    """,
    "impact": """
    impact considering the potential scientific, technological, and societal impact.
    """,
}


def create_analyst_agent(
    analyst: Literal["novelty", "feasibility", "impact"],
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a analyst agent that evaluates the hypothesis."""

    analyst_prompt = PromptTemplate.from_template(ANALYST_PROMPT)

    llm = get_model(model, **kwargs)
    chain = analyst_prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        logger.info(f"Starting {analyst} analysis")

        # Get the literature information from the response
        literature = state["literature"]

        # Run the chain
        logger.info(f"Running {analyst} analysis chain")
        response = chain.invoke(
            {
                **state,
                "literature": literature,
                "analysis_type": analyst,
                "task": PROMPT_TASK_TEMPLATES[analyst],
            }
        )
        logger.info(f"{analyst} analysis completed successfully")

        return {
            "messages": [add_role(response, analyst)],
            analyst: response.content,
        }

    return {"agent": agent}
