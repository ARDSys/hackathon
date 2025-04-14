from abc import ABC, abstractmethod
from ard.hypothesis.hypothesis import Hypothesis
from hackathon.autogen.llm_config import get_llm_config
from autogen import AssistantAgent, UserProxyAgent
from typing import Optional
import numpy as np
from .Module import Module
from .TournamentMatrixCompareModule import TournamentMatrixCompareModule
# Navitagte to hackathon/autogen/llm_config.py to configure the LLMs
class LLMQueryModule(Module):
    def __init__(
        self,
        model_name: str = "small",
        agent_name: str = "llm_agent",
        system_message: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.config = get_llm_config(model_name)

        self.agent = AssistantAgent(
            name=agent_name,
            llm_config=self.config,
            system_message=system_message,
            description=description,
        )

        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            is_termination_msg=lambda x: True
        )

    def forward(self, prompt: str) -> str:
        self.user_proxy.initiate_chat(self.agent, message=prompt)
        return self.agent.chat_messages[self.user_proxy][-1]["content"]
class LLMHypothesisCompare(Module):
    def __init__(
        self,
        query_module: LLMQueryModule,
        extraction_module: Optional[LLMQueryModule] = None,
    ):
        self.query_module = query_module,
        self.extraction_module = extraction_module if extraction_module else query_module
        self.prompt_template = """
        Analyze the two medical hypotheses provided below. Compare them thoroughly based on the criteria of Novelty, Verifiability, and Significance. Determine which hypothesis presents a potentially stronger case for further investigation or potential impact, providing a clear, evidence-based justification for your conclusion.

        Hypotheses to Compare:

            Hypothesis A: {hypothesis_1}
            Hypothesis B: {hypothesis_2}

        Evaluation Criteria & Instructions:

        Carefully analyze each hypothesis individually against the following criteria. Then, explicitly compare Hypothesis A and Hypothesis B on each criterion before providing your overall assessment.

            Novelty:
                Analyze A & B: To what extent does each hypothesis propose a new idea, mechanism, correlation, or approach within its specific medical field? Does it challenge existing paradigms, fill a significant knowledge gap, or primarily build incrementally on existing research?
                Compare: Which hypothesis introduces a more original or potentially transformative concept compared to the current understanding or standard practice?

            Verifiability / Testability:
                Analyze A & B: How feasible is it to design experiments, clinical trials, observational studies, or data analyses to empirically test each hypothesis? Are the necessary tools, technologies, patient populations, or data sources reasonably accessible? Are the core concepts measurable? Are there significant ethical or practical barriers to testing?
                Compare: Which hypothesis appears more readily testable or falsifiable using current or foreseeable scientific methods and resources? Which presents fewer obstacles to verification?

            Significance / Potential Impact:
                Analyze A & B: If proven true, what is the potential magnitude of the impact of each hypothesis? Consider its potential to:
                    Change fundamental understanding of a disease or biological process.
                    Lead to new diagnostic tools or strategies.
                    Result in novel preventative measures or treatments.
                    Improve clinical practice or patient outcomes significantly.
                    Address a major unmet medical need or affect a large patient population.
                Compare: Which hypothesis, if validated, promises a greater positive impact on science, medicine, or public health?

        Synthesis and Conclusion:

            Overall Comparison: Summarize the relative strengths and weaknesses of Hypothesis A and Hypothesis B across all three criteria (Novelty, Verifiability, Significance).
            Final Assessment: Based on your comparative analysis, which hypothesis do you assess as being "better" or more promising overall?
            Justification: Provide a concise but well-reasoned justification for your final assessment. Acknowledge trade-offs (e.g., one might be more novel but harder to verify, while the other is more easily testable but potentially less impactful). The "better" hypothesis should represent the most compelling balance according to the criteria.

        Output Format:

        Please structure your response clearly:

            Brief summary of Hypothesis A and Hypothesis B.
            Analysis and Comparison for Novelty.
            Analysis and Comparison for Verifiability.
            Analysis and Comparison for Significance.
            Overall Comparison Summary.
            Final Assessment and Justification.
        """
        self.extraction_template = """
        {reasoning}
        Based on reasoning above decide whether first or second hypothesis is better.
        Write **ONLY ONE WORD** to output as your answer: FIRST or SECOND.
        """
    def forward(self, hypothesis1: str, hypothesis2: str) -> str:
        llm_response = self.query_module(
            self.prompt_template.format(
                hypothesis_1=hypothesis1,
                hypothesis_2=hypothesis2
            )
        )
        answer = self.extraction_module(
            self.extraction_template.format(
                reasoning=llm_response
            )
        )
        #if llm_reponse ends in FIRST return 1 else return 2
        if answer.endswith("FIRST"):
            return 1
        else:
            return 2
class PointBasedTournament(Module):
    def forward(self, matrix: np.array):
        #matrix[i][j]==1 means i beats j
        self.result = np.zeros(matrix.shape[0])
        for i in range(matrix.shape[0]):
            for j in range(i+1,matrix.shape[1]):
                if matrix[i][j] == -np.inf:
                    continue
                self.result[i] += matrix[i][j] #add score to i
                self.result[j] += -matrix[i][j] #add negative score to j
        #sort indices based on result
        indices = np.argsort(self.result)[::-1]
        return indices
class EloBasedTournament(Module):
    def forward(self, matrix: np.array,numberofround: int = 1, match_cancel_prob: float = 0.2):
        #matrix[i][j]==1 means i beats j
        elo = np.full(matrix.shape[0], 1000) #initial elo rating
        matches = []
        for i in range(matrix.shape[0]):
            for j in range(i+1,matrix.shape[1]):
                if matrix[i][j] == -np.inf:
                    continue
                matches.append((i,j))
        for _ in range(numberofround):
            np.random.shuffle(matches)
            for i,j in matches:
                if np.random.rand() < match_cancel_prob:
                    continue
                if matrix[i][j] == 1:
                    winner = i
                    loser = j
                else:
                    winner = j
                    loser = i
                #update elo rating
                expected_winner = 1/(1+10**((elo[loser]-elo[winner])/400))
                expected_loser = 1/(1+10**((elo[winner]-elo[loser])/400))
                elo[winner] += 32*(1-expected_winner)
                elo[loser] += 32*(0-expected_loser)
        #sort indices based on elo
        indices = np.argsort(elo)[::-1]
        return indices
class SwissTournamentModule(Module):
    def __init__(
        self,
        matrix_compare_module: TournamentMatrixCompareModule,
        k_value: int = 5
    ):
        self.matrix_compare_module = matrix_compare_module
        self.k_value = k_value
    def forward(self, hypothesis: list[Hypothesis]):
        if len(hypothesis) % 2 != 0:
            raise ValueError("Hypothesis list must be even")
        elo = np.full(len(hypothesis), 1000)
        matches = []
        numer_of_rounds = int(np.ceil(np.log2(len(hypothesis))*self.k_value))
        for i in range(numer_of_rounds):
            matches=[] #stores which matches are played in this round
            indices = np.argsort(elo)[::-1]
            for j in range(0, len(hypothesis), 2):
                matches.append((indices[j], indices[j+1]))
            results = self.matrix_compare_module(hypothesis,matches)
            for i,j in matches:
                if results[i][j] > 0: #to be changed
                    winner = i
                    loser = j
                else:
                    winner = j
                    loser = i
                expected_winner = 1/(1+10**((elo[loser]-elo[winner])/400))
                expected_loser = 1/(1+10**((elo[winner]-elo[loser])/400))
                elo[winner] += 32*(1-expected_winner)
                elo[loser] += 32*(0-expected_loser)
        #sort indices based on elo
        indices = np.argsort(elo)[::-1]
        return indices