from typing import Any, Dict, Literal

from langchain.prompts import PromptTemplate
from loguru import logger

from ..hypothesis_tree import HypothesisNode, HypothesisTree
from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

SCIENTIST_PROMPT = """You are a sophisticated scientist trained in scientific research and innovation. 

Based on the previous hypothesis and its critique, your task is to refine and improve the hypothesis. Consider the UCT score which indicates how promising this research direction is (higher score = more promising).

Previous hypothesis UCB score: {ucb_score:.3f}

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
        
        # Get or create the hypothesis tree
        tree = HypothesisTree.from_state(state)
        current_node = tree.current_node
        
        if not current_node:
            logger.warning("No current hypothesis node found, creating new one")
            current_node = HypothesisNode(hypothesis=state["hypothesis"])
            tree.root = current_node
            tree.current_node = current_node
        
        # Calculate UCT-related metrics using global total_visits
        uct_score = current_node.uct_score(tree.total_visits)
        
        # Run the chain with UCT information
        response = chain.invoke({
            **state,
            "uct_score": uct_score,
            "visits": current_node.visits,
            "total_visits": tree.total_visits
        })
        
        # Create and add new node using tree manager
        new_node = tree.add_child(current_node, response.content)
        tree.current_node = new_node
        
        logger.info("Hypothesis refined successfully")
        
        return {
            **state,
            "hypothesis": response.content,
            "messages": [add_role(response, "hypothesis_refiner")],
            "hypothesis_tree": tree,
            "iteration": state.get("iteration", 0) + 1,
        }

    return {"agent": agent}
