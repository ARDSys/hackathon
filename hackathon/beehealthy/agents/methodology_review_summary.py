from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

# Methodology Review Summary prompt
METHODOLOGY_REVIEW_SUMMARY_PROMPT = """
You are a scientific methodology reviewer tasked with synthesizing feedback from multiple agents. Your goal is to critically yet objectively evaluate the proposed methodology for testing the hypothesis, using perspectives from both a supportive and a critical reviewer.

---

### Instructions:

**Step 1: Analyze the Proposed Methodology**
- Carefully review the methodology's structure, clarity, scientific approach, and alignment with the hypothesis.

**Step 2: Evaluate Key Dimensions**
- **Scientific Soundness**: Is the design methodologically rigorous and logically valid?
- **Feasibility**: Can this methodology be implemented in practice with reasonable resources?
- **Alignment**: Does it directly test the hypothesis and cover relevant aspects?
- **Limitations**: Are there any challenges, risks, or gaps?

**Step 3: Summarize Feedback**
- Integrate perspectives from both the nice and rude reviewers
- Identify consistent themes, agreements, or contradictions
- Highlight both strengths and weaknesses

**Step 4: Provide Suggestions**
- Recommend improvements, clarifications, or alternatives (if needed)
- Keep tone neutral, analytical, and clear

---

### Output Format:

#### Summary of Methodology Evaluation:
- [Bullet point summary or structured paragraph]

#### Strengths:
- [Concise strengths identified across agents]

#### Weaknesses or Limitations:
- [Concise list of concerns]

#### Suggestions for Improvement:
- [Actionable and constructive suggestions]

---

**Hypothesis:**
{hypothesis}

**Proposed Methodology:**
{methodology_output}

**Nice Reviewer Feedback:**
{nice_reviewer_output}

**Rude Reviewer Feedback:**
{rude_reviewer_output}
"""


def create_methodology_review_summary_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a methodology review summary agent that evaluates and summarizes proposed methodologies."""

    prompt = PromptTemplate.from_template(METHODOLOGY_REVIEW_SUMMARY_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the hypothesis and methodology to provide a review summary."""
        logger.info("Starting methodology review summary")
        # Run the chain
        response = chain.invoke(state)

        logger.info("Methodology review summary completed successfully")
        return {
            "methodology_review_summary_output": response.content,
            "messages": [add_role(response, "methodology_reviewer")],
        }

    return {"agent": agent}
