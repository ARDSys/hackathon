from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

SCIENTIST_PROMPT = """You are a sophisticated scientist trained in scientific research and innovation. 
    
Given a hypothesis, critical feedback on the hypothesis, and definitions and relationships acquired from a comprehensive knowledge graph, your task is to refine the hypothesis. Your response should not only demonstrate deep understanding and rational thinking but also explore imaginative and unconventional applications of these concepts. 
    
Analyze the critical feedback deeply and carefully, then craft an improved hypothesis that incorporates the feedback.

The refined hypothesis should be well-defined, have novelty, be feasible, have a well-defined purpose and clear components. Your hypothesis should be as detailed as possible. Ensure it is both innovative and grounded in logical reasoning, capable of advancing our understanding or application of the concepts provided.

Remember, the value of your response lies in scientific discovery, new avenues of scientific inquiry, and potential technological breakthroughs, with detailed and solid reasoning.

Hypothesis:
{hypothesis}

Critical Feedback:
{critique}

Definitions and Relationships (Context):
{context}

Graph:
{subgraph}
"""


def create_hypothesis_refiner_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a hypothesis refiner agent that refines a hypothesis based on critical feedback."""

    prompt = PromptTemplate.from_template(SCIENTIST_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Refine a research hypothesis based on critical feedback."""
        logger.info("Starting hypothesis refinement")
        # Run the chain
        response = chain.invoke(state)

        content = response.content
        logger.info("Hypothesis refined successfully")

        return {
            "hypothesis": content,
            "messages": [add_role(response, "hypothesis_refiner")],
            "iteration": state.get("iteration", 0) + 1,
        }

    return {"agent": agent}
