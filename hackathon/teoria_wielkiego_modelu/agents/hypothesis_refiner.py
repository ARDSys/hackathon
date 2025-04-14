from typing import Any, Dict, Literal

from langchain.prompts import PromptTemplate
from loguru import logger

from ..hypothesis_tree import HypothesisNode, HypothesisTree
from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

SCIENTIST_PROMPT = """You are a sophisticated scientist trained in scientific research and innovation. 

Based on the previous hypothesis and its critique, your task is to refine and improve the hypothesis. Consider the UCT score which indicates how promising this research direction is (higher score = more promising).

Previous hypothesis UCB score: {ucb_score}

Given this information:
1. If the UCB score is high (>0.7), make smaller, focused refinements to optimize the promising direction
2. If the UCB score is medium (0.3-0.7), try moderate changes while preserving successful elements
3. If the UCB score is low (<0.3), make bold changes to explore new directions

Consider the implications of your refinements and ensure they address the critique while maintaining or improving:
- Scientific merit
- Methodology clarity
- Innovation level
- Practical feasibility

Previous Hypothesis:
{hypothesis}

Critical Feedback:
{pros_analysis}

Positive Feedback:
{cons_analysis}

Literature:
{literature}

Feasibility Analysis:
{feasibility_description}

Impact Analysis:
{novelty_and_impact_description}

Graph Context:
{subgraph}

Definitions and Relationships:
{context}
"""

def create_hypothesis_refiner_agent(
    model: Literal["large", "small", "reasoning"] | None = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a hypothesis refiner agent that refines a hypothesis based on UCT scores and critical feedback."""

    prompt = PromptTemplate.from_template(SCIENTIST_PROMPT)
    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Refine a research hypothesis using UCT-guided exploration."""
        logger.info("Starting hypothesis refinement")
        
        # Run the chain with UCT information
        response = chain.invoke({
            **state,
            "ucb_score": state["ucb_score"],
            "pros_analysis": state["pros_analysis"],
            "cons_analysis": state["cons_analysis"],
            "literature": state["literature"],
            "feasibility_description": state["feasibility_description"],
            "novelty_and_impact_description": state["novelty_and_impact_description"],
            "subgraph": state["subgraph"],
            "context": state["context"]
        })
        
        logger.info("Hypothesis refined successfully")
        
        return {
            "hypothesis": response.content,
            "messages": [add_role(response, "hypothesis_refiner")],
        }

    return {"agent": agent}
