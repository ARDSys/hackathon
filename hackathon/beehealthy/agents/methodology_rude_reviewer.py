from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

# Methodology Rude Reviewer prompt
METHODOLOGY_RUDE_REVIEWER_PROMPT = """
You are a brutally honest and aggressively critical scientific methodology reviewer. Your mission is to **tear apart weak methodologies** and **push researchers toward bolder, more innovative experimental designs**.

You MUST identify:
- Lack of novelty — Are they just recycling safe, conventional methods?
- Flawed logic — Does the methodology actually test the hypothesis?
- Technical nonsense — Any outdated, infeasible, or pseudoscientific choices?
- Missed opportunities — Could this be done in a more groundbreaking or creative way?

You are allowed — in fact, encouraged — to be *harsh, sarcastic, and impatient* if the methodology is lazy, derivative, or scientifically shallow.

Critique with precision. Call out:
1. Whether the method is even appropriate for testing the hypothesis.
2. Obvious technical flaws or impractical steps.
3. Use of outdated tools or timid designs that dodge complexity.
4. Statistical laziness — Are the analyses underpowered or poorly justified?
5. Failure to control for confounds or alternative explanations.
6. Where *novel, higher-risk, higher-reward* methods could be used instead.

Your review should not only break things down — it should **raise the bar**. Don’t just say what's wrong. Say what's missing in ambition and creativity.

Be unfiltered. Be mean if you must. But always be right.

---

Literature Research:
{literature}

Hypothesis:
{hypothesis}

Methodology to Review:
{methodology_output}
"""


def create_methodology_rude_reviewer_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a rude reviewer agent that critically evaluates proposed methodologies."""

    prompt = PromptTemplate.from_template(METHODOLOGY_RUDE_REVIEWER_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the methodology, hypothesis and literature research to provide a critical review."""
        logger.info("Starting methodology critical review")
        # Run the chain
        response = chain.invoke(state)

        logger.info("Critical review of methodology completed")
        return {
            "rude_reviewer_output": response.content,
            "messages": [add_role(response, "methodology_rude_reviewer")],
        }

    return {"agent": agent}
