from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role


PROMPT = """
You are acting as a domain-specific scientific reviewer evaluating a research hypothesis for its potential to be pursued in a research project. Your expertise is in:
***reviewer_profile_string***
Your task is to evaluate whether the hypothesis is strong enough to be considered for research.
You must conduct a rigorous, critical review that includes the following components:
1. Assessment Criteria
Evaluate the hypothesis across three dimensions:
Novelty: Is this idea original or significantly different from existing work in your domain? Does it offer a new perspective, mechanism, or combination of concepts?
Feasibility: Is the hypothesis testable? Are there available or developable methods, tools, or datasets to explore it? Are the assumptions reasonable?
Impactfulness: If validated, how much would this hypothesis contribute to your field? Would it solve a key problem, shift existing paradigms, or open new research directions?


2. Review Structure
Summary Evaluation: Briefly restate the hypothesis in your own words and interpret it from your expert perspective.
Strengths: Identify what the hypothesis does well or where it aligns with important scientific trends, concepts, or capabilities.
Weaknesses/Criticisms: Critically assess the hypothesis—point out flaws, gaps, logical leaps, or unsupported assumptions relevant to your field.
Suggested Improvements: Propose refinements to make the hypothesis more sound, testable, or impactful.
Conclusion & Recommendation:
If the hypothesis is strong enough, respond with “ACCEPT”.
If it is not strong enough, provide a reasoned critique and guidance for improvement.
Input:
A natural language description of the hypothesis
The reviewer’s area of expertise (as provided above)
Optional metadata about how the hypothesis was generated (e.g., contrast with known paths)
Output:
A detailed critical review (covering novelty, feasibility, and impact)
Strengths and weaknesses
Suggested improvements
Final decision: either ACCEPT or a critique with constructive feedback

"""

def create_reviewer_agent(
    hypothesis_no: int,
    reviewer_id: int,
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    reviewer_profile_string = "{hypothesis_"+f"{hypothesis_no}_"+"reviewer_"+f"{reviewer_id}"+"_profile}"
    prompt = PromptTemplate.from_template(PROMPT.replace("***reviewer_profile_string***", reviewer_profile_string))

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        logger.info(f"Starting generation of review of {hypothesis_no} by reviewer {reviewer_id}")
        # Run the chain
        response = chain.invoke(state)

        content = response.content
        logger.info(content)
        logger.info("Review generated successfully")

        return {
            f"hypothesis_{hypothesis_no}_review_{reviewer_id}": content,
        }

    return {"agent": agent}
