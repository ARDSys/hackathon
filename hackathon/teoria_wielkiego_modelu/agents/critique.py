from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

CRITIQUE_PROMPT = """You are a critical analysis agent whose role is to find and articulate potential weaknesses and counterarguments AGAINST the given hypothesis.
Base on the feasibility_score, feasibility_description and novelty_and_description_score.
Your task is to thoroughly analyze the hypothesis and identify potential flaws, limitations, and areas of concern.

Focus on:
1. Methodological weaknesses and scientific inconsistencies
2. Gaps in reasoning based on existing literature
3. Potential confounding factors and implementation risks
4. Practical limitations identified in feasibility assessment

Hypothesis to analyze:
{hypothesis}

Available Literature:
{literature}

Feasibility Score:
{feasibility_score}

Feasibility Description:
{feasibility_description}

Novelty and impact description:
{novelty_and_impact_score}

Provide a detailed critical analysis, highlighting specific concerns and potential counterarguments."""

def create_critique_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a critique agent that identifies potential weaknesses in the hypothesis."""

    prompt = PromptTemplate.from_template(CRITIQUE_PROMPT)
    model = get_model(model, **kwargs)
    chain = prompt | model

    def agent(state: HypgenState) -> HypgenState:
        """Find and articulate arguments against the hypothesis."""
        logger.info("Starting critique analysis")
        
        response = chain.invoke({
            "hypothesis": state["hypothesis"],
            "literature": state["literature"],
            "feasibility_score": state["feasibility_score"],
            "feasibility_description": state["feasibility_description"],
            "novelty_and_impact_score": state["novelty_and_impact_score"]
        })
        
        logger.info("Critique analysis completed successfully")
        
        return {
            **state,
            "cons_analysis": response.content,
            "messages": [add_role(response, "critique")]
        }

    return {"agent": agent}