import json
from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

EXPERIMENT_REVIEWER_PROMPT = """
You are an AI expert in experiments, research design, and practical scientific implementation. 
You are given an experimental plan developed to test a scientific hypothesis.

Your task is to critically assess the feasibility of executing the proposed experiment in the real world, based on current technological, logistical, ethical, financial, and methodological constraints.

You may use the {literature} to understand how similar experiments are designed. 
Also use common sense and real-world knowledge to assess the feasibility and practicality of the experiment.
"feasibility_score":  A numeric score (0–100) representing how feasible the experiment is to conduct in practice with current capabilities, where 0 is completely infeasible and 10 is fully feasible without major obstacles.

You are evaluating the following experimental plan:
{experiment_plan}

Please respond **strictly in the following JSON format**. Please, Do not output anything else:

{
  "feasibility_score": <integer between 0 and 100>,
  "feasibility_description": "<detailed explanation justifying the score, highlighting strengths, limitations, and recommendations>"
}
"""


def create_experiment_reviewer_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:

    experiment_planner_prompt = PromptTemplate.from_template(EXPERIMENT_REVIEWER_PROMPT)

    llm = get_model(model, **kwargs)
    chain = experiment_planner_prompt | llm

    def agent(state: HypgenState) -> HypgenState:

        attempt = 0
        while True:
                # Run the chain
            logger.info("Running experiment_planner analysis chain")
            response = chain.invoke({**state,
                    "literature": state["literature"],
                    "experiment_plan": state["experiment_plan"]
                    })
            logger.info("Experiment_planner completed successfully")
            try:
                parsed = json.loads(response.content)
                if "feasibility_score" in parsed and "feasibility_description" in parsed:
                    break  
            except json.JSONDecodeError:
                pass

            logger.warning(f"Attempt {attempt + 1} failed to parse valid JSON.")
            attempt += 1
            

        feasibility_score = parsed["feasibility_score"]
        feasibility_description = parsed["feasibility_description"]

        return {
            "feasibility_description": feasibility_description,
            "feasibility_score" : feasibility_score,
            "messages": [add_role(response, "experiment_reviewer")],
        }

    return {"agent": agent}
