from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

SCIENTIST_PROMPT = """You are a sophisticated scientist trained in scientific research and innovation. 
    
Given the definitions and relationships acquired from a comprehensive knowledge graph, your task is to synthesize a novel research hypothesis. Your response should not only demonstrate deep understanding and rational thinking but also explore imaginative and unconventional applications of these concepts. 
    
Analyze the graph deeply and carefully, then craft a detailed hypothesis that investigates a likely groundbreaking aspect of the knowledge graph.

Consider the implications of your hypothesis and predict the outcome or behavior that might result from this line of investigation. Your creativity in linking these concepts to address unsolved problems or propose new, unexplored areas of study, emergent or unexpected behaviors, will be highly valued.

The hypothesis should be well-defined, has novelty, is feasible, has a well-defined purpose and clear components. Your hypothesis should be as detailed as possible. Ensure it is both innovative and grounded in logical reasoning, capable of advancing our understanding or application of the concepts provided.

Remember, the value of your response lies in scientific discovery, new avenues of scientific inquiry, and potential technological breakthroughs, with detailed and solid reasoning.

Graph:
{subgraph}

Definitions and Relationships:
{context}
"""


def create_hypothesis_generator_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a hypothesis generator agent that creates research proposals based on ontologist analysis."""

    prompt = PromptTemplate.from_template(SCIENTIST_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Generate a research hypothesis based on the ontologist's analysis."""
        logger.info("Starting hypothesis generation")
        # Run the chain
        response = chain.invoke(state)

        content = response.content
        logger.info("Hypothesis generated successfully")

        return {
            "hypothesis": content,
            "messages": [add_role(response, "hypothesis_generator")],
            "iteration": state.get("iteration", 0) + 1,
        }

    return {"agent": agent}
