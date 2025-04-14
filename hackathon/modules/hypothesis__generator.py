from typing import List, Set
from ard.knowledge_graph import KnowledgeGraph
from ard.hypothesis import Hypothesis
import numpy as np
import random as rng
from hackathon.modules.Module import Module
from hackathon.modules.LLMQueryModule import LLMQueryModule
from hackathon.modules.GenerateGraphModule import GraphPaperLinkerWithLLMSummary
'''
Hipothesis: 

'''

class HypothesisGenerator:
    def __init__(self, model_name="small", agent_name = "hypothesis_generator"):
        self.llm = LLMQueryModule(model_name=model_name, agent_name = agent_name)

    def generate_hypothesis(self, subgraph) -> str:
        title = "XD"
        statement = "XD"

        subgraph.save_to_file("subgraph.json")

        INPUT_GRAPH_FILE = "subgraph.json" # Path to the input graph file
        OUTPUT_FILE_TEMPLATE = "TEST{graph_name}_enriched_with_summaries.json" # Template for output

        linker = GraphPaperLinkerWithLLMSummary(
            llm_model_name="small",
            output_filename_template=OUTPUT_FILE_TEMPLATE
        )

    

        return Hypothesis(
            title=title,
            statement=statement,
            source=subgraph,
            method=self,
            metadata={},
        )
    

if __name__ == "__main__":
    # Example usage
    model_name = "small"
    agent_name = "hypothesis_generator"
    hg = HypothesisGenerator(model_name=model_name, agent_name=agent_name)
    
    # Assuming `subgraph` is a valid subgraph object
    subgraph = KnowledgeGraph()
    subgraph.load_from_file("data/Bridge_Therapy.json")
    hypothesis = hg.generate_hypothesis(subgraph)
    print(hypothesis)