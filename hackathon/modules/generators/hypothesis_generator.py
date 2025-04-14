'''

class HypothesisGenerator:
    def __init__(self, model_name="small", agent_name = "hypothesis_generator"):
        self.llm = LLMQueryModule(model_name=model_name, agent_name = agent_name)

    def generate_hypothesis(self, subgraph) -> str:
        # Find paths between the start and end node 
        start_node = "xd"#subgraph['start']
        end_node = "xd" #subgraph['end']
        path_descriptions = ["xd0", "xd1", "xd2"] #subgraph['path']
         # Final formatted prompt
        prompt = f"""
You are given a scientific knowledge graph connecting phenomena via logical and causal relationships, including supporting paper abstracts.

Your task is to propose a new, insightful **scientific hypothesis** that could explain or connect the phenomena between:
- **Start:** {start_node}
- **End:** {end_node}

Here are some paths from the graph:
-----------------------
{chr(10).join(f"Path {i+1}:\n{p}\n" for i, p in enumerate(path_descriptions[rng.randint(0, 2)]))} ##
-----------------------

Based on these paths, suggest a novel hypothesis or mechanism that might explain how '{start_node}' leads to '{end_node}'.

**Only output the hypothesis.**
"""
    
        # Get the response from the LLM
        statement = self.llm.forward(prompt)
        
        title = "Hypothesis title"
        return [title, statement]
    
'''


from hackathon.modules.Module import Module
from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph
from dataclasses import dataclass
from typing import Dict, Any, List
import random as rng
from hackathon.modules.LLMQueryModule import LLMQueryModule
import json

@dataclass
class TemplateGenerator(HypothesisGeneratorProtocol):
    llm_name: Any
    
    # Return some Hypothesis that will then compete in tournament
    def run(self, subgraph: Subgraph, num_hypothesis: int) -> List[Hypothesis]:

        with open("NOWEBridge_Therapy_enriched_with_summaries.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        # Prepare a list to store the edge summaries
        edge_summaries = []
        statements = []
        # Extract triplet_string and llm_summary from each entry
        for entry in data:
            bucket = []
            triplet_string = entry.get('triplet_string', 'No triplet_string')
            for group in entry.get('paper_analysis', []):
                bucket.append(group.get('llm_summary'))
            edge_summaries.append([bucket, triplet_string])


            # For example, you want to generate 10 question statements
            for i in range(num_hypothesis):
                question = []
                # Iterate over the edge summaries and generate questions
                for x in edge_summaries:
                    random_index = rng.randint(0,2)
                    summaries = x[0][random_index]  # The list of LLM summaries for each triplet
                    triplet_string = x[1]  # The corresponding triplet_string
                    # Combine summaries into a cohesive statement/question
                    summary_text = " ".join(summaries)

                    question_prompt = f"Based on the following summary related to the triplet: '{triplet_string}', what is the relationship between the phenomena described?"
                    # Append both the generated question and the summary to the question list
                    question.append(f"Summary: {summary_text}\nQuestion: {question_prompt}")
                # Append the generated question to the final statements list
                statements.append(question)
        
        return [Hypothesis(
            title="Microglial-Mediated Neuroinflammation as a Link Between Systemic Inflammation and Alzheimer's Pathology",
            statement="Systemic inflammation activates microglia, leading to neuroinflammation that promotes both amyloid beta accumulation and tau pathology, accelerating Alzheimer's disease progression.",
            source=subgraph,
            method=self,
            references=[
                "Smith et al. (2019). Neuroinflammation and Neurodegeneration. Journal of Neuroscience, 40(1), 123-145.",
                "Chen, J. & Wong, T. (2021). Microglial Activation in Alzheimer's Disease. Nature Reviews Neuroscience, 22(4), 210-228."
            ],
            metadata={
                "confidence": 0.85,
                "generated_by": "MIKO",
                "agent_contributions": {
                    "research_agent": "...",
                    "critic_agent": "..."
                }
            }
        )] * 3

    def __str__(self) -> str:
        return "TemplateGenerator"

    def to_json(self) -> Dict[str, Any]:
        return {
            "name": str(self),
            "type": "template_generator"
        }

subgraph = Subgraph.load_from_file("Bridge_Therapy_enriched_with_summaries.json")