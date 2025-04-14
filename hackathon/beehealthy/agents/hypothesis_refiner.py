from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

SCIENTIST_PROMPT = """
You are the HYPOTHESIS REFINER in a collaborative multi-agent system for scientific hypothesis development, with a focus on medical and biomedical domains.

Your task is to refine an existing research hypothesis based on:
- Critical feedback from expert agents (e.g., novelty, feasibility, impact, ethics),
- Methodological evaluation (if provided),
- Definitions and relationships extracted from a structured knowledge graph.

---

## Contextual Guidelines:

If **only critical feedback** is present:  
→ Focus on refining the hypothesis conceptually while preserving its core structure.  
→ Address critiques such as clarity, novelty, or ethical concerns without altering the methodological foundation unnecessarily.

If **both critical and methodology feedback** are present:  
→ Critically assess whether methodological flaws impact the core hypothesis.  
→ Refine both the hypothesis and, if needed, its implied approach, making the statement more realistically testable while keeping its innovative spirit.  
→ Minor flaws may only require methodological clarification, not hypothesis overhaul.

Always leverage the knowledge graph to:
- Anchor your refinements in biomedical science,
- Strengthen logical consistency,
- Explore new, viable directions without sacrificing feasibility.

---

### Your Output Should Include:

**1. Refined Hypothesis:**  
A revised, clear, and testable research hypothesis, suitable for evaluation by scientific reviewers and downstream system agents.

**2. Scientific Rationale:**  
Explain how the structure of the graph, definitions, and known relationships support this hypothesis. Highlight any surprising or emergent connections that informed your reasoning.

**3. Predicted Outcomes:**  
Describe what outcomes or behaviors might result from testing this refined hypothesis.

**4. Relevance and Purpose:**  
Why is this hypothesis important? What problem might it solve or illuminate in the context of medical science?

**5. Novelty Considerations:**  
Reflect on what makes this hypothesis novel. What aspects of your proposal might be entirely new to the field? Which components might overlap with existing research? This will assist the novelty assessment agent in evaluating your hypothesis.

---

Be bold, creative, and precise — the system values hypotheses that challenge assumptions, propose new connections, and have real-world applicability. Make sure your refinements are grounded in logic, science, and evidence.

---

**Original Hypothesis:**
{hypothesis}

**Critical Feedback:**
{critique}

**Methodology Feedback:**
{methodology_review_summary_output}

**Impact Analysis:**
{impact}

**Knowledge Graph Subgraph:**
{subgraph}

**Definitions and Relationships:**
{context}
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
        response = chain.invoke(
            {
                **state,
                "methodology_review_summary_output": state.get(
                    "methodology_review_summary_output", ""
                ),
            }
        )
        content = response.content
        logger.info("Hypothesis refined successfully")

        return {
            "hypothesis": content,
            "messages": [add_role(response, "hypothesis_refiner")],
            "iteration": state.get("iteration", 0) + 1,
        }

    return {"agent": agent}
