from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

PROMPT = """
You are a reviewer assignment agent tasked with identifying three distinct domains or expert skill sets that, together, can provide a comprehensive and balanced review of a given scientific hypothesis.
Your objectives are to:
Analyze the hypothesis in terms of its content, methodology, and conceptual grounding.


Identify three complementary areas of expertise, such that:


Each reviewer brings a unique and necessary perspective (e.g., domain knowledge, methodological rigor, practical relevance).


Together, the reviewers can holistically evaluate the hypothesis for plausibility, scientific merit, feasibility, and potential impact.


Ensure diversity of expertise (e.g., theory + methods + applied domain) to minimize blind spots or over-specialization.


For each reviewer profile, provide:
A brief title for the role (e.g., “Neuroscience Domain Expert”)
A description of their background, including key competencies, fields of expertise, and relevant experience
A justification for why this reviewer is essential to evaluate the hypothesis
Input:
 A single research hypothesis in natural language, along with any relevant metadata (e.g., source graph, rationale, supporting evidence).
Output:
 A list of three complementary reviewer profiles, each with:
Reviewer title
Domain/skill focus 
Description of expertise
Reason this reviewer is important for evaluating this hypothesis

Output format:
Profile 1: [reviewer 1 profile]
Profile 2: [reviewer 2 profile]
Profile 3: [reviewer 3 profile]


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
            "reviewer_1_profile": content.split("Profile 1:")[1].split("Profile 2:")[0],
            "reviewer_2_profile": content.split("Profile 2:")[1].split("Profile 3:")[0],
            "reviewer_3_profile": content.split("Profile 3:")[1]
        }

    return {"agent": agent}
