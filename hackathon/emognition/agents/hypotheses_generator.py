from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role
from ...consts import num_initial_hypotheses

PROMPT = f"""
You are a sophisticated scientist trained in scientific research and innovation. 
    
Given the definitions and relationships acquired from a comprehensive knowledge graph, as well as summarized knowledge obtained from literature review, your task is to synthesize a novel research hypothesis. Your response should demonstrate deep understanding and rational thinking, as well as explore imaginative and unconventional applications of these concepts. 
    
Analyze the graph’s paths deeply and carefully, then craft {num_initial_hypotheses} detailed hypothesis that investigates a likely groundbreaking aspect of the knowledge graph.

Consider the implications of your hypothesis and predict the outcome or behavior that might result from this line of investigation. Your creativity in linking these concepts to address unsolved problems or propose new, unexplored areas of study, emergent or unexpected behaviors, will be highly valued.

The hypothesis should be well-defined, have novelty, be feasible, have a well-defined purpose and clear components. Your hypothesis should be as detailed as possible. Ensure it is both innovative and grounded in logical reasoning, capable of advancing our understanding or application of the concepts provided.

Remember, the value of your response lies in scientific discovery, new avenues of scientific inquiry, and potential technological breakthroughs, with detailed and solid reasoning.

Output the {num_initial_hypotheses} generated hypotheses, each in the following format, where <hypothesis id> is the ordering of the hypotheses, and <hypothesis text> is the text of the hypothesis:
Hypothesis <hypothesis id>: <hypothesis text>.
""" + """
Paths:
{paths}

Summarized knowledge:
{knowledge}
"""


def create_hypotheses_generator_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    prompt = PromptTemplate.from_template(PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        logger.info("Starting hypothesis generation")
        # Run the chain
        response = chain.invoke(state)

        content = response.content
        logger.info(content)

        logger.info("Hypotheses generated successfully")
        return {
            "hypothesis": content
        }

    return {"agent": agent}
