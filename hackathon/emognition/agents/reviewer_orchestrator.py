from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

PROMPT = """
You are an expert in interdisciplinary science facilitation.
Your task is to analyze the following scientific hypothesis and identify three distinct scientific domains or specializations that are most relevant for a rigorous expert-level review of this hypothesis. These should represent different expert perspectives, ideally spanning across methodological, theoretical, and applied aspects.
Instructions:
Extract exactly three domains or specializations.
Each domain should be specific (e.g., computational neuroscience, affective computing, statistical learning theory).
Avoid overly general fields (e.g., biology, computer science) unless the hypothesis itself is extremely broad.
Aim for diversity in perspective: include complementary angles such as empirical validation, theoretical framing, and computational methods.
Hypothesis: {hypothesis}
Output format:
Domain 1: [name] — [short justification and detailed profile of the domain 1 expert]
Domain 2: [name] — [short justification and detailed profile of the domain 2 expert]
Domain 3: [name] — [short justification and detailed profile of the domain 3 expert]

"""


def create_reviewer_orchestrator_agent(
        hypothesis_no: int,
        model: Optional[Literal["large", "small", "reasoning"]] = None,
        **kwargs,
) -> Dict[str, Any]:
    prompt = PromptTemplate.from_template(PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        logger.info("Starting reviewer identification")
        # Run the chain
        response = chain.invoke(state)

        content = response.content
        logger.info("Reviewers identified successfully")

        return {
            "reviewer_1_profile": content.split("Domain 1:")[1].split("Domain 2:")[0],
            "reviewer_2_profile": content.split("Domain 2:")[1].split("Domain 3:")[0],
            "reviewer_3_profile": content.split("Domain 3:")[1]
        }

    return {"agent": agent}
