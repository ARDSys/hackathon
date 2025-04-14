from hackathon.modules.Module import Module
from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph
from dataclasses import dataclass
from typing import Dict, Any, List
import concurrent.futures
import random
from hackathon.modules.LLMChatModule import LLMChatModule
import json

@dataclass
class SkibidiGenerator(HypothesisGeneratorProtocol):
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, subgraph, subgraph_json):
        subgraph_str = ""
        for triplet in subgraph_json:
            analysis = random.choice(triplet['paper_analysis'])
            subgraph_str += f"**{triplet['triplet_string']}**\n{analysis['llm_summary']}\n\n"
        with open('hackathon/prompts/comparator_system.txt', 'r', encoding='UTF-8') as f:
            system_prompt = f.read()
        
        llm = LLMChatModule(self.model_name, "hypothesis_generator", system_prompt)
        prompt_file = random.choice([
            'hackathon/prompts/generator1a.txt',
            'hackathon/prompts/generator1b.txt'
        ])
        with open(prompt_file, 'r', encoding='UTF-8') as f:
            llm( f.read().replace("{subgraph}", subgraph_str).replace("{start_node}", subgraph.start_node).replace("{end_node}", subgraph.end_node) )
        with open('hackathon/prompts/generator2.txt', 'r', encoding='UTF-8') as f:
            ans = llm(f.read())
        
        start = ans.find('[')
        end = ans.rfind(']')
        return json.loads(ans[start:end+1])
        

    def run(self, subgraph: Subgraph, subgraph_json: any, num_hypothesis: int, max_workers: int = 16) -> List[Hypothesis]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            hyps = list(executor.map(lambda _: self.generate(subgraph, subgraph_json), range(num_hypothesis)))
        result = []
        for lst in hyps:
            for ent in lst:
                result.append(Hypothesis(
                    title=ent['title'],
                    statement=ent['statement'],
                    references=ent['references'],
                    source=subgraph,
                    method=self,
                    metadata={
                        "generated_by": "MIKO"
                    }
                ))
        return result

    def __str__(self) -> str:
        return "SkibidiGenerator"

    def to_json(self) -> Dict[str, Any]:
        return {
            "name": str(self),
            "type": "skibidi_generator"
        }
