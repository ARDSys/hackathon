from typing import List
from hackathon.modules.EvaluationModule import GeneralEvaluationScore

def evaluate_hypotheses(hypotheses: List[str]):
    score_fn = GeneralEvaluationScore(model_names=["gemini-2.0-flash"])
    
    return score_fn(hypotheses)
