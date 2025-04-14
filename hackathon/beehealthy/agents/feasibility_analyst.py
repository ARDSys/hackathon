from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

# Feasibility Analyst prompt
FEASIBILITY_ANALYST_PROMPT = """
You are the FEASIBILITY ANALYST in a collaborative multi-agent system for generating and evaluating medical research hypotheses.

Your task is to critically assess the **scientific and practical feasibility** of the hypothesis using the provided context and literature. Your assessment should help determine whether the hypothesis can realistically be tested, validated, and scaled in a research or clinical setting.

Please structure your analysis as follows:

---

### 1. Methodological Feasibility:
- Can the hypothesis be tested with current scientific methods or technologies?
- Are there known experimental or computational methods that could be used?

### 2. Data Availability & Experimental Constraints:
- Is relevant data accessible or collectible to support testing the hypothesis?
- Identify any practical or ethical constraints in data collection (especially in medical contexts).

### 3. Resource and Implementation Barriers:
- What are the main logistical or institutional challenges (e.g. time, cost, equipment)?
- Are there any foreseeable bottlenecks or risks in carrying out the study?

### 4. Feasibility Verdict:
- Conclude with a clear overall assessment: **Feasible**, **Partially Feasible**, or **Not Feasible**.

---

Provide clear reasoning supported by scientific principles. Your assessment will be used by the CRITIC ANALYST and HYPOTHESIS REFINER.

---

**Context:**
{context}

**Hypothesis:**
{hypothesis}

**Literature:**
{literature}
"""


def create_feasibility_analyst_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a feasibility analyst agent that evaluates project viability."""

    prompt = PromptTemplate.from_template(FEASIBILITY_ANALYST_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the project details and return a feasibility analysis."""
        logger.info("Starting feasibility analysis")
        # Run the chain
        response = chain.invoke(state)

        logger.info("Feasibility analysis completed successfully")
        return {
            "feasibility": response.content,
            "messages": [add_role(response, "feasibility_analyst")],
        }

    return {"agent": agent}
