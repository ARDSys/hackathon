from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

CRITIQUE_PROMPT = """You are a critical analysis agent whose role is to find and articulate potential weaknesses and counterarguments AGAINST the given hypothesis.
Your task is to thoroughly analyze the hypothesis and identify potential flaws, limitations, and areas of concern.

Focus on:
1. Methodological weaknesses
2. Alternative explanations
3. Potential confounding factors
4. Implementation challenges
5. Gaps in reasoning or evidence

Hypothesis to analyze:
{hypothesis}

Available Literature:
{literature}

Context:
{context}

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
            **state,
            "hypothesis": state["hypothesis"],
            "literature": state["literature"],
            "context": state["context"]
        })
        
        logger.info("Critique analysis completed successfully")
        
        return {
            "cons_analysis": response.content,
            "messages": [add_role(response, "critique")]
        }

    return {"agent": agent}