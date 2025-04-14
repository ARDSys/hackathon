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
{novelty_and_impact_description}

Feasibility Assessment:
{feasibility_description}


Critique:
{pros_analysis}

{cons_analysis}
"""

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
        
        
        # Run the chain with tree statistics
        response = chain.invoke({
            "hypothesis": state["hypothesis"],
            "novelty_and_impact_description": state["novelty_and_impact_description"],
            "feasibility_description": state["feasibility_description"],
            "pros_analysis": state["pros_analysis"],
            "cons_analysis": state["cons_analysis"]
        })
        
        logger.info("Summary generated successfully")
        return {
            "summary": response.content,
            "title": state.get("title", "")
        }

    return {"agent": agent}
