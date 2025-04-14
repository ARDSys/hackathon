from typing import List
import numpy as np
import hackathon.utils as utils

from hackathon.modules.Module import Module
from hackathon.modules.LLMQueryModule import LLMQueryModule

# Provides a measure of how likely LLMs consider the hypothesis
class BasicCorrectnessScore(Module):
    def __init__(self, model_names: List[str]):
        self.llm_modules = []

        for name in model_names:
            llm_module = LLMQueryModule(
                model_name=name,
                agent_name=f"hypothesis_correctness_evaluator",
                system_message="You are a scientific evaluator AI. Respond with a reasoning chain followed by a numerical score between 0 and 1 indicating the likelihood a hypothesis is scientifically correct.",
                description="Evaluates the correctness of scientific hypotheses with reasoning."
            )
            self.llm_modules.append(llm_module)

        self.prompt_template = """
You are a scientific evaluator AI. You are provided with a research hypothesis. Your job is to evaluate the scientific **likelihood** that this hypothesis is correct, based on established scientific knowledge and logical consistency.

You must reason step-by-step through the following criteria:
1. Alignment with existing scientific principles (physics, chemistry, biology, etc.).
2. Internal logical consistency of the hypothesis and mechanisms.
3. The plausibility of the mechanisms described.
4. Coherence with known experimental or theoretical results.
5. Absence of contradictions with physical laws or chemical/biological constraints.

Write 1-2 sentences analyzing each of these five aspects in order. Then, **on a new line at the very end**, provide **a single numerical score between 0 and 1**, where:
- 0 means the hypothesis is certainly incorrect.
- 0.5 means the hypothesis is speculative or unclear.
- 1 means the hypothesis is highly likely to be correct.

Only include the score as the final output, on the last line of your response.

Hypothesis:
{hypothesis}
"""

    def forward(self, hypothesis: str) -> float:
        scores = []
        prompt = self.prompt_template.format(hypothesis=hypothesis)

        for module in self.llm_modules:
            response = module(prompt)
            try:
                last_line = response.strip().splitlines()[-1].split()[-1]
                score = float(last_line.strip())
                if 0.0 <= score <= 1.0:
                    scores.append(score)
            except ValueError:
                continue

        if scores:
            return sum(scores) / len(scores)
        return 0.5

# Provides a measure of how similar two hypotheses are
class HypothesisSimilarityScore(Module):
    def __init__(self, model_names: List[str]):
        self.llm_modules = []

        for name in model_names:
            llm_module = LLMQueryModule(
                model_name=name,
                agent_name="hypothesis_similarity_evaluator",
                system_message="You are a scientific similarity evaluator. Respond with reasoning and a similarity score between 0 and 1.",
                description="Compares two scientific hypotheses for conceptual similarity."
            )
            self.llm_modules.append(llm_module)

        self.prompt_template = """
You are a scientific AI tasked with comparing two research hypotheses. Your goal is to evaluate how conceptually similar they are, based on the mechanisms, scientific domains, and overall ideas involved.

Analyze the following five aspects, one or two sentences each:
1. Are they rooted in the same scientific field or subfield?
2. Do they describe similar biological/chemical/physical systems?
3. Are the underlying mechanisms or processes comparable?
4. Is the reasoning or theoretical basis similar?
5. Do they aim to explain the same or closely related phenomena?

After analyzing each aspect, **on a new line at the very end**, provide **a single similarity score from 0 to 1**, where:
- 0 means completely unrelated,
- 0.5 means moderately related,
- 1 means highly similar or near-identical ideas.

Only include the score as the final output, on the last line of your response.

Hypothesis 1:
{hypothesis_1}

Hypothesis 2:
{hypothesis_2}
"""

    def forward(self, hypothesis_1: str, hypothesis_2: str) -> float:
        scores = []
        prompt = self.prompt_template.format(hypothesis_1=hypothesis_1, hypothesis_2=hypothesis_2)

        for module in self.llm_modules:
            response = module(prompt)
            try:
                last_line = response.strip().splitlines()[-1].split()[-1]
                score = float(last_line.strip())
                if 0.0 <= score <= 1.0:
                    scores.append(score)
            except ValueError:
                continue

        if scores:
            return np.mean(scores)
        return 0.5


# Provides a measure of how interesting LLMs consider the hypothesis
class HypothesisInterestScore(Module):
    def __init__(self, model_names: List[str]):
        self.llm_modules = []

        for name in model_names:
            llm_module = LLMQueryModule(
                model_name=name,
                agent_name="hypothesis_interest_evaluator",
                system_message="You are a scientific evaluator AI. Respond with a reasoning chain followed by a numerical score between 0 and 1 indicating how interesting or novel a hypothesis is.",
                description="Evaluates the scientific interest and novelty of hypotheses with reasoning."
            )
            self.llm_modules.append(llm_module)

        self.prompt_template = """
You are a scientific evaluator AI. You are provided with a research hypothesis. Your job is to evaluate how **interesting, novel, or potentially impactful** this hypothesis is in the context of scientific exploration.

You must reason step-by-step through the following criteria:
1. Originality: Is the hypothesis new or an unexplored perspective on existing ideas?
2. Theoretical significance: Could it meaningfully expand or challenge existing theories?
3. Practical implications: Could this lead to new technologies, treatments, or applications?
4. Curiosity factor: Does the hypothesis stimulate curiosity or open new research questions?
5. Potential to generate follow-up studies or experiments.

Write 1-2 sentences analyzing each of these five aspects in order. Then, **on a new line at the very end**, provide **a single numerical score between 0 and 1**, where:
- 0 means the hypothesis is not interesting or original.
- 0.5 means the hypothesis has some novelty or relevance.
- 1 means the hypothesis is highly original, exciting, or impactful.

Only include the score as the final output, on the last line of your response.

Hypothesis:
{hypothesis}
"""

    def forward(self, hypothesis: str) -> float:
        scores = []
        prompt = self.prompt_template.format(hypothesis=hypothesis)

        for module in self.llm_modules:
            response = module(prompt)
            try:
                last_line = response.strip().splitlines()[-1].split()[-1]
                score = float(last_line.strip())
                if 0.0 <= score <= 1.0:
                    scores.append(score)
            except ValueError:
                continue

        if scores:
            return sum(scores) / len(scores)
        return 0.5    
    
class GeneralEvaluationScore(Module):
    def __init__(self, model_names: List[str]):
        self.model_names = model_names
        
        self.hypothesis_interest_score = HypothesisInterestScore(model_names=model_names)
        self.hypothesis_similarity_score = HypothesisSimilarityScore(model_names=model_names)
        self.basic_correctness_score = BasicCorrectnessScore(model_names=model_names)
    
    def forward(self, hypotheses: List[str]) -> float:
        interest_scores = []
        correctness_scores = []
        for hypothesis in hypotheses:
            interest_score = self.hypothesis_interest_score(hypothesis)
            correctness_score = self.basic_correctness_score(hypothesis)
            
            interest_scores.append(interest_score)
            correctness_scores.append(correctness_score)
        
        interest_score = np.mean(interest_scores)
        correctness_score = np.mean(correctness_scores)
        
        similarity_grid = np.zeros((len(hypotheses),len(hypotheses)))
        for i in range(len(hypotheses)):
            for j in range(i+1,len(hypotheses)):
                hypothesis1 = hypotheses[i]
                hypothesis2 = hypotheses[j]
                
                similarity = self.hypothesis_similarity_score(hypothesis1, hypothesis2)
                
                similarity_grid[i][j] = similarity
                similarity_grid[j][i] = similarity
        
        softmax_scores = utils.softmax(similarity_grid, axis=-1)
        similarity_scores = np.sum(similarity_grid * softmax_scores,axis=-1)
        dissimilarity_scores = 1 - similarity_scores

        # This division is related to the fact that many moderetely
        # similar hypotheses provide relativily similar information
        dissimilarity_scores = dissimilarity_scores / (1 + np.sum(similarity_grid,axis=-1))

        dissimilarity_score = np.mean(dissimilarity_scores)
        
        return interest_score * correctness_score * dissimilarity_score

