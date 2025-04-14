from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

DEVIL_ADVOCATE_PROMPT = """You are a devil's advocate agent whose role is to find and articulate strong arguments SUPPORTING the given hypothesis.
Base on the feasibility_score, feasibility_description and novelty_and_description_score.
Your task is to thoroughly analyze the hypothesis and provide compelling evidence and reasoning that supports its validity. Analyze it.

Focus on:
1. Scientific merit and logical consistency
2. Alignment with existing literature and known mechanisms
3. Potential positive implications and applications
4. Novel insights and innovative aspects

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

Provide a detailed analysis of supporting arguments, backed by evidence where possible."""

def create_devil_advocate_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a devil's advocate agent that finds arguments supporting the hypothesis."""

    prompt = PromptTemplate.from_template(DEVIL_ADVOCATE_PROMPT)
    model = get_model(model, **kwargs)
    chain = prompt | model

    def agent(state: HypgenState) -> HypgenState:
        """Find and articulate arguments supporting the hypothesis."""
        logger.info("Starting devil's advocate analysis")
        
        response = chain.invoke({
            **state,
            "hypothesis": state["hypothesis"],
            "literature": state["literature"],
            "context": state["context"],
            "feasibility_score": state["feasibility_score"],
            "feasibility_description": state["feasibility_description"],
            "novelty_and_impact_score": state["novelty_and_impact_score"]
        })
        
        logger.info("Devil's advocate analysis completed successfully")
        
        return {
            "pros_analysis": response.content,
            "messages": [add_role(response, "devil_advocate")]
        }

    return {"agent": agent}