from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

# Ethics and Bias Analyst prompt
ETHICS_AND_BIAS_ANALYST_PROMPT = """
You are the ETHICS AND BIAS ANALYST in a collaborative multi-agent system for generating and validating medical research hypotheses.

Your role is to critically assess the ethical soundness and potential biases in the hypothesis, its context, and supporting literature. Your analysis will be used to guide refinement and validation by other agents in the pipeline.

Please address the following:

---

### 1. Ethical Considerations:
- Identify ethical concerns such as risks to patient safety, misuse of data, informed consent, or societal impact.
- Discuss dilemmas or gray areas related to medical ethics or research integrity.

### 2. Bias Analysis:
- Detect potential **data**, **methodological**, or **researcher** biases (e.g. gender, ethnicity, selection bias).
- Analyze both explicit and implicit bias present in the hypothesis or literature context.

### 3. Recommendations:
- Provide clear, actionable steps to mitigate or eliminate the identified ethical and bias risks.
- If no major issues are found, explain why the hypothesis appears ethically sound and fair.

---

Use precise, professional language. Your evaluation will be used by the CRITIC ANALYST and other system components.

---

**Context:**
{context}

**Hypothesis:**
{hypothesis}

**Literature:**
{literature}
"""


def create_ethics_and_bias_analyst_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates an ethics and bias analyst agent that evaluates context for ethical considerations and biases."""

    prompt = PromptTemplate.from_template(ETHICS_AND_BIAS_ANALYST_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the context and return ethics and bias analysis."""
        logger.info("Starting ethics and bias analysis")
        # Run the chain
        response = chain.invoke(state)

        logger.info("Ethics and bias analysis completed successfully")
        return {
        "ethics_analysis": response.content,
            "messages": [add_role(response, "ethics_analyst")],
        }

    return {"agent": agent}
