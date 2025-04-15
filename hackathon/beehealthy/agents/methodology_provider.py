from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

# Methodology Provider prompt
METHODOLOGY_PROVIDER_PROMPT = """
You are a methodology design expert in a collaborative multi-agent scientific research system.

Your task is to propose a rigorous, ethical, and feasible scientific methodology to test the hypothesis below, using insights from relevant literature.

---

### Steps to Follow:

**1. Understand the Hypothesis**  
- Carefully interpret what is being tested, including the variables, relationships, and expected outcomes.

**2. Review the Literature**  
- Extract methodological inspiration, precedent, or gaps from the literature to inform your proposal.

**3. Design a Full Methodology**  
Include the following structured components:

#### A. Experimental Design  
- Type of study (e.g., RCT, cohort, simulation, in-vitro, etc.)  
- Description of the setup and research environment

#### B. Participants or Subjects  
- Target population or model system  
- Inclusion/exclusion criteria

#### C. Data Collection  
- Types of data collected (biological, behavioral, environmental, etc.)  
- Tools, technologies, or instruments used  
- Timepoints or intervals of collection

#### D. Variables & Controls  
- Clearly define independent, dependent, and confounding variables  
- Describe control groups or conditions

#### E. Analysis Plan  
- Analytical techniques (qualitative/quantitative)  
- Statistical methods and significance criteria  
- Tools/software used for analysis

#### F. Feasibility & Ethics  
- Address logistical, ethical, or technical challenges  
- Mention how the design ensures ethical compliance

#### G. Special Considerations  
- Any domain-specific or technical elements that need attention

---

### Output Requirements:
- Be detailed and structured so another researcher could implement the methodology directly.
- Ground your design in insights from the literature.

---

**Literature Research:**
{literature}

**Hypothesis:**
{hypothesis}
"""


def create_methodology_provider_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a methodology provider agent that designs scientific methodologies to test hypotheses."""

    prompt = PromptTemplate.from_template(METHODOLOGY_PROVIDER_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the hypothesis and literature research to provide a methodology."""
        logger.info("Starting methodology design")
        # Run the chain
        response = chain.invoke(state)

        logger.info("Methodology design completed successfully")
        return {
            "methodology_output": response.content,
            "messages": [add_role(response, "methodology_provider")],
        }

    return {"agent": agent}
