import json
from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState

JUDGE_PROMPT = """
You are a synthesis and evaluation agent tasked with analyzing a collection of generated research hypotheses and selecting the top 3 candidates based on a multi-criteria evaluation.

You will be provided with a set of hypotheses, which may vary in their novelty, level of support, and scientific ambition.

Your goals are to:

Evaluate each hypothesis along the following three dimensions:
Novelty: How original is the idea compared to existing, well-established research paths?
Feasibility: How practical is it to investigate or test this hypothesis, given current methods, data availability, and conceptual clarity?
Impactfulness: If validated, how significant could this hypothesis be for advancing understanding, opening new research directions, or solving important problems?
For each hypothesis, provide:
A score (1–5) for each dimension: Novelty, Feasibility, and Impactfulness.
A short justification for each score.
Optional notes on trade-offs (e.g., “Very novel but low feasibility”).
Select and rank the top 3 hypotheses that offer the best overall value (not necessarily the highest total score — balance and strategic potential matter).

Input:
A list of research hypotheses, each with:
Natural language summary
Supporting rationale
Any metadata (e.g., citation stats, literature contrast, domain relevance)

Output:
A ranked list of the top 3 hypotheses

Hypotheses:
{hypothesis}

Paths:
{paths}

Summarized knowledge:
{knowledge}

Return response formatted exactly as below:

TOP 1 HYPOTHESIS TEXT:  [top 1 hypothesis text]
TOP 2 HYPOTHESIS TEXT: [top 2 hypothesis text]
TOP 3 HYPOTHESIS TEXT: [top 3 hypothesis text]

"""


def create_hypotheses_judge_agent(
        model: Optional[Literal["large", "small", "reasoning"]] = None,
        **kwargs,
) -> Dict[str, Any]:
    prompt = PromptTemplate.from_template(JUDGE_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(s: HypgenState) -> HypgenState:
        logger.info("Judging started")
        # Run the chain
        response = chain.invoke(s)
        print(response.content)
        prefixandRest = response.content.split("TOP 1 HYPOTHESIS TEXT:")
        oneAndRest = prefixandRest[1].split("TOP 2 HYPOTHESIS TEXT:")
        one = oneAndRest[0]
        twoAndThree = oneAndRest[1].split("TOP 3 HYPOTHESIS TEXT:")
        two = twoAndThree[0]
        three = twoAndThree[1]

        return {
            "hypothesis_1_text": one,
            "hypothesis_2_text": two,
            "hypothesis_3_text": three,
        }


    return {"agent": agent}
