from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger
from pydantic import BaseModel

from ..llm.utils import get_model
from ..state import HypgenState

# Summary prompt
SUMMARY_PROMPT = """You are a skilled scientific writer.

Given a hypothesis and it's novelty, feasibility, and impact analysis, write a concise summary of both the hypothesis and the analysis.

Here is an example structure for our response, in the following format

{{
### Hypothesis
...

### Novelty Assessment:  Not novel/Somewhat novel/Novel/Very novel
...

### Feasibility Assessment:  Not feasible/Somewhat feasible/Feasible
...

### Impact Assessment:  Not impactful/Somewhat impactful/Impactful/Very impactful
...
}}

Here is the hypothesis and the analysis:
Hypothesis:
{hypothesis}

Novelty Assessment:
{novelty}

Feasibility Assessment:
{feasibility}

Impact Assessment:
{impact}
"""


class HypothesisSummary(BaseModel):
    title: str
    summary: str


def create_summary_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates an ontologist agent that analyzes and defines concepts from a knowledge graph."""

    prompt = PromptTemplate.from_template(SUMMARY_PROMPT)

    llm = get_model(model, **kwargs).with_structured_output(HypothesisSummary)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the hypothesis and the analysis and return a summary."""
        logger.info("Starting summary generation")
        # Run the chain
        response = chain.invoke(state)

        logger.info("Summary generated successfully")
        return {
            "summary": response.summary,
            "title": response.title,
        }

    return {"agent": agent}
