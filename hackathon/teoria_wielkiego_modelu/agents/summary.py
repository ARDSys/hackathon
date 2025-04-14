from typing import Any, Dict, Literal

from langchain.prompts import PromptTemplate
from loguru import logger

from ..hypothesis_tree import HypothesisNode, HypothesisTree
from ..llm.utils import get_model
from ..state import HypgenState

SUMMARY_PROMPT = """You are a skilled scientific writer.

Given a hypothesis exploration tree and its analysis, write a concise summary of the research direction exploration.

Here is an example structure for our response:

{{
### Final Hypothesis
[The final refined hypothesis]

### Exploration Statistics
- Total iterations: {iterations}
- Best UCT score achieved: {best_score:.3f}
- Total hypotheses explored: {total_explored}
- Average hypothesis score: {avg_score:.3f}

### Analysis Summary
#### Novelty Assessment: Not novel/Somewhat novel/Novel/Very novel
[Summary of novelty analysis]

#### Feasibility Assessment: Not feasible/Somewhat feasible/Feasible
[Summary of feasibility analysis]

#### Impact Assessment: Not impactful/Somewhat impactful/Impactful/Very impactful
[Summary of impact analysis]

### Exploration Path
[Brief description of how the hypothesis evolved through iterations]

### Future Directions
[Suggestions for further exploration based on the UCT scores]
}}

Current Hypothesis:
{hypothesis}

Novelty Assessment:
{novelty}

Feasibility Assessment:
{feasibility}

Impact Assessment:
{impact}

Critique:
{critique}
"""

def collect_tree_statistics(tree: HypothesisTree) -> Dict[str, Any]:
    """Collect statistics about the hypothesis exploration tree"""
    if not tree or not tree.root:
        return {
            "total_nodes": 0,
            "total_score": 0,
            "max_score": 0,
            "path": []
        }
    
    def traverse_node(node: HypothesisNode) -> Dict[str, Any]:
        stats = {
            "total_nodes": 1,
            "total_score": node.average_score,
            "max_score": node.average_score,
            "path": [{
                "score": node.average_score,
                "visits": node.visits,
                "hypothesis": node.hypothesis
            }]
        }
        
        if node.children:
            for child in node.children:
                child_stats = traverse_node(child)
                stats["total_nodes"] += child_stats["total_nodes"]
                stats["total_score"] += child_stats["total_score"]
                stats["max_score"] = max(stats["max_score"], child_stats["max_score"])
                stats["path"].extend(child_stats["path"])
                
        return stats
    
    return traverse_node(tree.root)

def create_summary_agent(
    model: Literal["large", "small", "reasoning"] | None = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a summary agent that provides a comprehensive overview of the hypothesis exploration."""

    prompt = PromptTemplate.from_template(SUMMARY_PROMPT)
    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the hypothesis exploration and return a comprehensive summary."""
        logger.info("Starting summary generation")
        
        # Get the hypothesis tree from state
        tree = HypothesisTree.from_state(state)
        stats = collect_tree_statistics(tree)
        
        # Calculate aggregate metrics
        avg_score = stats["total_score"] / stats["total_nodes"] if stats["total_nodes"] > 0 else 0
        
        # Run the chain with tree statistics
        response = chain.invoke({
            **state,
            "iterations": state.get("iteration", 0),
            "best_score": stats["max_score"],
            "total_explored": tree.total_visits,
            "avg_score": avg_score,
            "exploration_path": stats["path"]
        })
        
        logger.info("Summary generated successfully")
        return {
            "summary": response.content,
            "title": state.get("title", ""),
            "exploration_stats": {
                "best_score": stats["max_score"],
                "total_explored": tree.total_visits,
                "avg_score": avg_score,
                "exploration_path": stats["path"]
            }
        }

    return {"agent": agent}
