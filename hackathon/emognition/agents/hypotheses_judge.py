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
A ranked list of the top 3 hypotheses, each with:
Scores for Novelty, Feasibility, and Impactfulness
Concise justification for selection
Notes on possible next steps or validation strategies

Hypotheses:
{hypotheses}

Paths:
{paths}

Summarized knowledge:
{knowledge}

Return response as a JSON and only JSON formatted as below:

{
    "hypothesis_1": {
        "text": "[hypothesis 1 text]",
        "novelty": "[hypothesis 1 novelty]",
        "feasibility": "[hypothesis 1 feasibility]",
        "impactfulness": "[hypothesis 1 impactfulness]",
    },
    "hypothesis_2": {
        "text": "[hypothesis 2 text]",
        "novelty": "[hypothesis 2 novelty]",
        "feasibility": "[hypothesis 2 feasibility]",
        "impactfulness": "[hypothesis 2 impactfulness]",
    },
    "hypothesis_3": {
        "text": "[hypothesis 3 text]",
        "novelty": "[hypothesis 3 novelty]",
        "feasibility": "[hypothesis 3 feasibility]",
        "impactfulness": "[hypothesis 2 impactfulness]",
    },
}
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
        judgeJson = json.loads(chain.invoke(
            {
                "hypotheses": s.hypothesis,
                "paths": s.paths,
                "knowledge": s.knowledge,
            }
        ))

        s["hypothesis_1_text"] = judgeJson["hypothesis_1"]["text"]
        s["hypothesis_1_novelty"] = judgeJson["hypothesis_1"]["novelty"]
        s["hypothesis_1_impactfullness"] = judgeJson["hypothesis_1"]["impactfulness"]
        s["hypothesis_1_feasibility"] = judgeJson["hypothesis_1"]["feasibility"]

        s["hypothesis_2_text"] = judgeJson["hypothesis_2"]["text"]
        s["hypothesis_2_novelty"] = judgeJson["hypothesis_2"]["novelty"]
        s["hypothesis_2_impactfullness"] = judgeJson["hypothesis_2"]["impactfulness"]
        s["hypothesis_2_feasibility"] = judgeJson["hypothesis_2"]["feasibility"]

        s["hypothesis_3_text"] = judgeJson["hypothesis_3"]["text"]
        s["hypothesis_3_novelty"] = judgeJson["hypothesis_3"]["novelty"]
        s["hypothesis_3_impactfullness"] = judgeJson["hypothesis_3"]["impactfulness"]
        s["hypothesis_3_feasibility"] = judgeJson["hypothesis_3"]["feasibility"]
        logger.info("Hypothesis was sentenced")
        return s

    return {"agent": agent}
