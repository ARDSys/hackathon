from typing import Any, Dict, Literal, Optional
import json

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role


NOVELTY_AND_IMPACT_REVIEWER_PROMPT = """
You are an AI scientific reviewer. You are provided with a scientific hypothesis and a body of related literature. 
Your task is to evaluate the novelty, potential impact, and scientific value of the hypothesis based on existing hypotheses and research.

Review **novelty** by assessing how closely the hypothesis aligns with or diverges from prior work. Does the hypothesis present something new or refine existing knowledge? You can use the provided literature: {literature} to help inform your evaluation.
Evaluate **impact** by considering the potential influence of the hypothesis on the field. How likely is it to drive further research, change current understanding, or lead to practical applications? You can reference the literature: {literature} to support your judgment.

The hypothesis is: {hypothesis}

Please respond **strictly in the following JSON format**:

```json
{
  "novelty_and_impact_score": <integer between 0 and 100>,
  "novelty_and_impact_description": "<description of the hypothesis's novelty and impact>"
}

"""


def create_experiment_reviewer_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:

    novelty_and_impact_reviewer_prompt = PromptTemplate.from_template(NOVELTY_AND_IMPACT_REVIEWER_PROMPT)

    llm = get_model(model, **kwargs)
    chain = novelty_and_impact_reviewer_prompt | llm

    def agent(state: HypgenState) -> HypgenState:

        attempt = 0
        while True:
                # Run the chain
            logger.info(f"Running novelty_and_impact_reviewer analysis chain")
            response = chain.invoke({**state,
                    "literature": state["literature"],
                    "hypothesis": state["hypothesis"]
                    })
            logger.info("novelty_and_impact_reviewer completed successfully")
            try:
                parsed = json.loads(response.content)
                if "novelty_and_impact_score" in parsed and "novelty_and_impact_description" in parsed:
                    break  
            except json.JSONDecodeError:
                pass

            logger.warning(f"Attempt {attempt + 1} failed to parse valid JSON.")
            attempt += 1
            

        novelty_and_impact_score = parsed["novelty_and_impact_score"]
        novelty_and_impact_description = parsed["novelty_and_impact_description"]

        return {
            "novelty_and_impact_score": novelty_and_impact_score,
            "novelty_and_impact_description" : novelty_and_impact_description,
            "messages": [add_role(response, "novelty_and_impact_reviewer")],
        }

    return {"agent": agent}
