from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

SCIENTIST_PROMPT = """
You are the HYPOTHESIS GENERATOR in a multi-agent system designed for scientific discovery, with a specialization in medical and biomedical research.

You are given a subgraph from a comprehensive knowledge graph, along with definitions and relationships that reflect current scientific understanding.

Your task is to:
1. Deeply analyze the graph structure and content.
2. Synthesize a **novel, medically-relevant research hypothesis** grounded in logic and scientific rationale.
3. Explore **unconventional connections**, **emergent relationships**, or **understudied phenomena**.
4. Present a well-defined and testable hypothesis, suitable for review by novelty, feasibility, and ethics agents.

---

### Your Output Should Include:

**1. Research Hypothesis:**  
A clear and detailed statement of the proposed hypothesis. It must be specific, innovative, and suitable for empirical investigation or modeling.

**2. Scientific Rationale:**  
Explain how the structure of the graph, definitions, and known relationships support this hypothesis. Highlight any surprising or emergent connections that informed your reasoning.

**3. Predicted Outcome or Behavior:**  
What new insight, pattern, or behavior would you expect if this hypothesis were tested and validated?

**4. Relevance and Purpose:**  
Why is this hypothesis important? What problem might it solve or illuminate in the context of medical science?

**5. Novelty Considerations:**  
Reflect on what makes this hypothesis novel. What aspects of your proposal might be entirely new to the field? Which components might overlap with existing research? This will assist the novelty assessment agent in evaluating your hypothesis.

---

### Emphasis on Novelty and Innovation:

**Think Outside the Box:**
* Challenge conventional wisdom and established paradigms
* Propose connections that have not been previously explored
* Consider cross-disciplinary approaches that bring new perspectives to medical challenges

**Avoid Common Patterns:**
* Do not simply restate well-established hypotheses or research directions
* Move beyond incremental improvements to existing theories
* Resist falling into predictable patterns of thinking

**Pursue Genuinely New Discoveries:**
* Aim for transformative ideas that could fundamentally change understanding or practice
* Look for blindspots in current research where breakthrough insights might be hiding
* Consider how emerging technologies might enable entirely new approaches

---

Ensure your hypothesis is logically sound, testable, and grounded in the graph — but don't be afraid to explore bold or unexpected directions. The system values hypotheses that lead to new research avenues or technological breakthroughs.

---

**Last hypothesis:**
{hypothesis}

**Knowledge Graph Subgraph:**
{subgraph}

**Definitions and Relationships:**
{context}

{novelty_feedback}
"""


def create_hypothesis_generator_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a hypothesis generator agent that creates research proposals based on ontologist analysis."""

    prompt = PromptTemplate.from_template(SCIENTIST_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Generate a research hypothesis based on the ontologist's analysis."""
        logger.info("Starting hypothesis generation")

        # Check if we have feedback from the novelty loop
        novelty_feedback = ""
        if "novelty_loop_output" in state and state["novelty_loop_output"]:
            logger.info("Including novelty feedback in hypothesis generation")
            novelty_feedback = f"""
            **Novelty Assessment Feedback:**
            The following feedback was provided by the novelty assessment. Please use this to improve the novelty of your hypothesis:
            
            {state["novelty_loop_output"]}
            """

        # Run the chain with novelty feedback if available
        response = chain.invoke(
            {
                **state,
                "novelty_feedback": novelty_feedback,
                "hypothesis": state.get("hypothesis", ""),
            }
        )

        content = response.content
        logger.info("Hypothesis generated successfully")

        return {
            "hypothesis": content,
            "messages": [add_role(response, "hypothesis_generator")],
            "iteration": state.get("iteration", 0),
        }

    return {"agent": agent}
