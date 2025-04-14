from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

PROMPT = """
You are an expert scientist tasked with evaluating a list of reviewed hypotheses and selecting the best one(s) based on a thorough analysis of their novelty, feasibility, and impact. Your role is to rank the hypotheses according to their overall quality and potential for scientific advancement, providing confidence scores to express your level of certainty in the rankings.
Your tasks:
Summarize each hypothesis in natural language, drawing from the reviews and the key aspects of each one (novelty, feasibility, impact).
Rank the hypotheses based on the following criteria:
Novelty: How original or groundbreaking is the hypothesis? Does it bring new concepts, methods, or insights?
Feasibility: How practically feasible is the hypothesis? Are the methods and data to test it realistic? Are any major barriers identified?
Impact: What is the potential significance of the hypothesis if it proves correct? Will it significantly advance the field or solve an important problem?


Assign confidence scores (on a scale of 1 to 10) for each hypothesis, reflecting your level of certainty about its overall strength and potential. Consider factors such as:
The strength of supporting evidence in the reviews.
Consensus or disagreement among reviewers.
Any highlighted strengths or weaknesses.


Rank the hypotheses from best to worst, providing the following for each hypothesis:
Summary of the hypothesis: A concise description.
Confidence score (1–10): Reflecting your confidence in the hypothesis' strength.
Explanation of the ranking: Brief reasoning for why the hypothesis ranks as it does, touching on novelty, feasibility, and impact.


Final output: A ranked list of hypotheses with:
Summary for each hypothesis
Confidence score
Explanation for the rank

Input:
A list of reviewed hypotheses, including:
Natural language summaries of the hypotheses.
Reviewer feedback, including strengths, weaknesses, feasibility, impact, and novelty assessments.
Final recommendations (ACCEPT or rejection with critique).

Input: 

Hypothesis 1:
{hypothesis_1_text}

Hypothesis 2:
{hypothesis_2_text}

Hypothesis 3:
{hypothesis_3_text}

Output must be formatted exactly as follows:

TEXT: [The best hypothesis text]
TITLE : [The title of best hypothesis text]
SUMMARY : [The summary of best hypothesis text]

"""


def create_final_judge_agent(
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
        final_hypothesis = content.split("TEXT:")[1].split("TITLE:")[0]
        title = content.split("TITLE:")[1].split("SUMMARY:")[0]
        summary = content.split("SUMMARY:")[1]
        logger.info(content)
        logger.info("Hypothesis generated successfully")

        return {
            "final_hypothesis": final_hypothesis,
            "summary": summary,
            "title": title,
        }

    return {"agent": agent}
