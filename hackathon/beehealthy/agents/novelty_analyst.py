from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

# Novelty Analyst prompt
NOVELTY_ANALYST_PROMPT = """You are a Novelty Analyst in a multi-agent system focused on generating and evaluating hypotheses in the medical and biomedical research domain.

Your primary responsibility is to assess the novelty of a given hypothesis based on a comprehensive literature review. You must determine whether the hypothesis introduces ideas, methods, or connections that represent a significant departure from existing knowledge.

Your Task:

Evaluate the novelty of the provided hypothesis by examining the literature context and research findings. Be thorough and precise in your reasoning.

Consider the following key novelty criteria:

1. Direct Prior Coverage:  
   - Has this hypothesis (or very similar ones) already been thoroughly studied?  
   - Are there many existing studies directly supporting or refuting it?

2. New Conceptual Links:  
   - Does the hypothesis propose a novel relationship between previously unrelated or loosely connected medical concepts?

3. Innovative Methodology or Framework:  
   - Does it introduce a new way to test, model, or conceptualize the medical question (e.g., new biomarkers, imaging methods, or AI tools)?

4. Challenge to Existing Paradigms:  
   - Does the hypothesis question established assumptions in clinical or theoretical practice?

What to Include in Your Analysis:

- A summary of findings from the literature that relate to the hypothesis.
- Any gaps, contradictions, or absences in existing studies that support the hypothesis's novelty.
- Mention of specific studies, review articles, or meta-analyses (cite or reference them by title, journal, or authorship as provided).
- A reasoned judgment based on the evidence.

Final Output Requirements:

- Provide a detailed novelty assessment (at least 2–3 paragraphs).
- Assign a novelty score from 1–10, based on the following scale:

1   – Already extensively studied, well-known  
3-4 – Minor variations of existing ideas  
5-6 – Somewhat new, but with partial prior exploration  
7-8 – Largely new direction or unexplored combination  
9-10 – Highly original, few if any prior studies exist

Evaluation Inputs:

Context to Analyze:  
{context}

Hypothesis:  
{hypothesis}

Literature Review Results:  
{literature}

Please ensure your analysis is rigorous and clearly structured. Use bullet points or numbered lists where helpful for clarity.
"""


def create_novelty_analyst_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a novelty analyst agent that evaluates the novelty of a hypothesis."""

    prompt = PromptTemplate.from_template(NOVELTY_ANALYST_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the literature research and ontology analysis to evaluate novelty."""
        logger.info("Starting novelty analysis")

        # Run the chain
        response = chain.invoke(state)

        logger.info("Novelty analysis completed successfully")
        return {
            "novelty": response.content,
            "messages": [add_role(response, "novelty_analyst")],
        }

    return {"agent": agent}
