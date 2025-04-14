from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role
from ...consts import num_hypotheses


PROMPT = """
You are serving as a meta-reviewer tasked with synthesizing and summarizing the input from three separate reviews of a given hypothesis. Your objective is to provide a final consolidated review that integrates the strengths, weaknesses, and suggestions from the individual reviewers into a single critical analysis.

Your tasks:
Summarize the three reviews: Integrate key points from each review, especially regarding novelty, feasibility, and impact. Identify any common themes, disagreements, or differing perspectives between the reviewers.
Provide a critical evaluation based on the following criteria:
Novelty: Based on the three reviews, assess whether the hypothesis brings something truly original to the field, or if it largely reiterates established ideas.
Feasibility: Summarize any concerns raised about the hypothesis's testability, assumptions, or practicality. Assess whether the hypothesis is feasible based on the reviewers' insights.
Impactfulness: Consolidate the views on the potential significance of the hypothesis in advancing the field. Does it solve a crucial problem, introduce new methodologies, or open novel areas of research?
Highlight the strengths and weaknesses: Based on the reviews, provide a summary of the hypothesis's strengths (e.g., innovative, well-grounded, practical) and weaknesses (e.g., speculative, lacking evidence, difficult to test).
Suggest improvements: Integrate any recommendations provided by the individual reviewers. Provide your own suggestions on how the hypothesis could be strengthened to increase its novelty, feasibility, or impact.

Final decision:
If the hypothesis is strong enough and the reviews are generally favorable, respond with “ACCEPT”.
If the hypothesis is not strong enough, provide a well-reasoned critique based on the reviewers' feedback, highlighting areas for improvement.

Input:
Three separate reviews of the hypothesis, each containing:
Assessment of novelty, feasibility, and impact.
Strengths and weaknesses.
Suggested improvements.
Final recommendation (ACCEPT or rejection with critique).

Output:
A consolidated, detailed critical review, covering:
Summary of novelty, feasibility, and impact
Strengths and weaknesses from the three reviews
Suggested improvements based on the reviews
Final decision: ACCEPT or detailed critique with constructive feedback

"""


def create_review_summarizer_agent(
    hypothesis_no: int,
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    PROMPT = """
        You are serving as a meta-reviewer tasked with synthesizing and summarizing the input from three separate reviews of a given hypothesis. Your objective is to provide a final consolidated review that integrates the strengths, weaknesses, and suggestions from the individual reviewers into a single critical analysis.
        
        Your tasks:
        Summarize the three reviews: Integrate key points from each review, especially regarding novelty, feasibility, and impact. Identify any common themes, disagreements, or differing perspectives between the reviewers.
        Provide a critical evaluation based on the following criteria:
        Novelty: Based on the three reviews, assess whether the hypothesis brings something truly original to the field, or if it largely reiterates established ideas.
        Feasibility: Summarize any concerns raised about the hypothesis's testability, assumptions, or practicality. Assess whether the hypothesis is feasible based on the reviewers' insights.
        Impactfulness: Consolidate the views on the potential significance of the hypothesis in advancing the field. Does it solve a crucial problem, introduce new methodologies, or open novel areas of research?
        Highlight the strengths and weaknesses: Based on the reviews, provide a summary of the hypothesis's strengths (e.g., innovative, well-grounded, practical) and weaknesses (e.g., speculative, lacking evidence, difficult to test).
        Suggest improvements: Integrate any recommendations provided by the individual reviewers. Provide your own suggestions on how the hypothesis could be strengthened to increase its novelty, feasibility, or impact.
        
        Final decision:
        If the hypothesis is strong enough and the reviews are generally favorable, respond with “ACCEPT”.
        If the hypothesis is not strong enough, provide a well-reasoned critique based on the reviewers' feedback, highlighting areas for improvement.
        
        Input:
        Three separate reviews of the hypothesis, each containing:
        Assessment of novelty, feasibility, and impact.
        Strengths and weaknesses.
        Suggested improvements.
        Final recommendation (ACCEPT or rejection with critique).
        
        Output:
        A consolidated, detailed critical review, covering:
        Summary of novelty, feasibility, and impact
        Strengths and weaknesses from the three reviews
        Suggested improvements based on the reviews
        Final decision: ACCEPT or detailed critique with constructive feedback
        
        """
    for i in range(num_hypotheses):
        PROMPT += f"""
            Review {i}: \n
            """ + "{" + f"hypothesis_{hypothesis_no}_review_{i}" + "}\n\n"
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
            f"critique_{hypothesis_no}": content,
        }

    return {"agent": agent}
