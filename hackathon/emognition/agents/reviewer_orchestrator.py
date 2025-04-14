from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

PROMPT = """
"""


def create_reviewer_orchestrator_agent(
    hypothesisNo: int,
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    prompt = PromptTemplate.from_template(PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        logger.info("Starting hypothesis generation")
        # Run the chain
        response = chain.invoke(state)

        content = response.content
        logger.info("Hypothesis generated successfully")

        return {
            "hypothesis": content,
        }

    return {"agent": agent}
