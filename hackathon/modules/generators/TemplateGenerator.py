from hackathon.modules.Module import Module
from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph
from dataclasses import dataclass
from typing import Dict, Any, List
from hackathon.modules.TournamentModule import SwissTournamentModule
from hackathon.modules.TournamentMatrixCompareModule import TournamentMatrixCompareModule
from hackathon.modules.HypothesisGenerator import HypothesisGenerator
from hackathon.modules.generators.SkibidiGenerator import SkibidiGenerator
import json

MODEL = "small"

@dataclass
class TemplateGenerator(HypothesisGeneratorProtocol):
    def run(self, subgraph: Subgraph) -> List[Hypothesis]:
        hg = HypothesisGenerator(model_name=MODEL, agent_name="hypothesis_generator")
        hg.generate_hypothesis(subgraph)
        path = "enriched_subgraph.json"

        with open(path, 'r', encoding='UTF-8') as f:
            subgraph_json = json.load(f)

        skibidi_generator = SkibidiGenerator("big")
        hypotheses = skibidi_generator.run(subgraph, subgraph_json, 25)

        tournament = SwissTournamentModule(TournamentMatrixCompareModule(subgraph, subgraph_json, model_name=MODEL))
        sorted_indices = tournament(hypotheses)
        best_indices = sorted_indices[0]

        best_hypotheses = [hypotheses[idx] for idx in best_indices]
        
        return best_hypotheses

    def __str__(self) -> str:
        return "TemplateGenerator"

    def to_json(self) -> Dict[str, Any]:
        return {
            "name": str(self),
            "type": "template_generator"
        }

if __name__ == "__main__":
    generator = TemplateGenerator()
    
    generator.run(Subgraph.load_from_file("eval/Autoimmunity.json")).save()
