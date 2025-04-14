from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

EXPERIMENT_PLANNER_PROMPT = """
You are an AI experiment planner collaborating with other AI research agents. You are given a scientific hypothesis proposed by your colleagues. 
They are uncertain whether this hypothesis is testable in the real world.
Your task is to generate a detailed, step-by-step experimental plan to test the hypothesis. 
The plan must be:
Feasible with current real-world technology and resources
Rigorous, aiming to determine the truth or falsehood of the hypothesis with extremely high confidence (≥99%)
Directly grounded in scientific precedent, drawing from the published literature provided in {literature}
You may reuse or adapt methodologies from relevant studies, but all elements must be tailored specifically to this hypothesis.

Instructions for output:
Do not include an introduction or preamble.
Present the experimental plan as clearly numbered steps.
Include specific details: sample sizes, controls, measurements, statistical methods, etc.
At the end, include a brief summary explaining how and why this experiment would confirm or refute the hypothesis.

The hypothesis is: {hypothesis}
"""


def create_experiment_planner_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:

    experiment_planner_prompt = PromptTemplate.from_template(EXPERIMENT_PLANNER_PROMPT)

    llm = get_model(model, **kwargs)
    chain = experiment_planner_prompt | llm

    def agent(state: HypgenState) -> HypgenState:

        # Run the chain
        logger.info("Running experiment_planner analysis chain")
        response = chain.invoke({
            "hypothesis": state["hypothesis"],
            "literature": state["literature"]
        })

        logger.info("Experiment_planner completed successfully")

        return {
            "experiment_plan": response.content,
            "messages": [add_role(response, "experiment_planner")]
        }


    return {"agent": agent}
