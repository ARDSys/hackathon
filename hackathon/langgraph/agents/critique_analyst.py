from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..hypothesis_tree import HypothesisNode, HypothesisTree
from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

CRITIC_AGENT_PROMPT = """You are a critical scientific reviewer. 
You are given a research hypothesis, together with the novelty, feasibility, and impact analysis.
Your task is to evaluate the hypothesis and provide a numerical score between 0.0 and 1.0, where:
- 0.0 represents a completely flawed or invalid hypothesis
- 1.0 represents an excellent hypothesis with high novelty, feasibility, and impact

Additionally, provide a thorough critical scientific review with:
1. Strengths (bullet points)
2. Weaknesses (bullet points)
3. Suggested improvements
4. Numerical scores for:
   - Scientific merit (0-1)
   - Methodology clarity (0-1)
   - Innovation level (0-1)
   - Practical feasibility (0-1)

Include logical reasoning and scientific approaches in your review.
Consider the literature when evaluating the hypothesis.

Your response should be structured as follows:
SCORE: [overall_score]

REVIEW:
[Your detailed review]

Literature:
{literature}

Hypothesis:
{hypothesis}

Novelty Analysis:
{novelty}

Feasibility Analysis:
{feasibility}

Impact Analysis:
{impact}
"""

def parse_score(response: str) -> float:
    """Extract numerical score from the response"""
    try:
        score_line = response.split('\n')[0]
        if score_line.startswith('SCORE:'):
            return float(score_line.replace('SCORE:', '').strip())
    except Exception:
        logger.warning("Failed to parse score, using default 0.5")
    return 0.5

def create_critique_analyst_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a critique analyst agent that evaluates the overall research proposal using UCT."""

    prompt = PromptTemplate.from_template(CRITIC_AGENT_PROMPT)
    model = get_model(model, **kwargs)
    chain = prompt | model

    def agent(state: HypgenState) -> HypgenState:
        """Evaluate the research proposal and provide critique with UCT scoring."""
        logger.info("Starting critique analysis")
        
        # Get or create the hypothesis tree
        tree = HypothesisTree.from_state(state)
        current_node = tree.current_node
        
        if current_node is None:
            current_node = HypothesisNode(hypothesis=state["hypothesis"])
            tree.root = current_node
            tree.current_node = current_node
            
        # Run the chain
        response = chain.invoke(state)
        score = parse_score(response.content)
        
        # Update node statistics using tree manager
        tree.visit_node(current_node, score)
        
        logger.info(f"Critique analysis completed with score: {score}")
        
        return {
            "critique": response.content,
            "messages": [add_role(response, "critique_analyst")],
            "hypothesis_tree": tree,
            "hypothesis_score": score
        }

    return {"agent": agent}
