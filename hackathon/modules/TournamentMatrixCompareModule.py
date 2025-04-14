from hackathon.modules.Module import Module
from hackathon.modules.LLMQueryModule import LLMQueryModule
from ard.hypothesis import Hypothesis
from typing import List, Tuple
import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from hackathon.modules.LLMChatModule import LLMChatModule
from ard.subgraph import Subgraph
import random

class TournamentMatrixCompareModule(Module):
    def __init__(self, subgraph: Subgraph, subgraph_json: any, model_name: str = "small", max_workers: int = 16):
        self.model_name = model_name
        self.max_workers = max_workers
        self.subgraph = subgraph

        self.subgraph_str = ""
        for triplet in subgraph_json:
            analysis = random.choice(triplet['paper_analysis'])
            self.subgraph_str += f"**{triplet['triplet_string']}**\n{analysis['llm_summary']}\n\n"

    def get_hyphotesis_str(self, h: Hypothesis):
        return f"**{h.title}**\n{h.statement}\nreferences:{'\n'.join(h.references)}"
    
    def compare(self, h1: Hypothesis, h2: Hypothesis):
        score = 0

        for prompt1, prompt2 in [('comparator1a.txt', 'comparator2a.txt'), ('comparator1b.txt', 'comparator2b.txt')]:
            try:
                with open('hackathon/prompts/comparator_system.txt', 'r', encoding='UTF-8') as f:
                    system_prompt = f.read()
                llm = LLMChatModule(self.model_name, "comparator", system_prompt)
                with open(f'hackathon/prompts/{prompt1}', 'r', encoding='UTF-8') as f:
                    txt = f.read()
                    # print('AAA FILE:')
                    # print(txt)
                    # print('AAA H1:')
                    # print(self.get_hyphotesis_str(h1))
                    # print('AAA REPLACED:')
                    # print(txt.replace("{h1}", self.get_hyphotesis_str(h1)))
                    # print('AAA')

                    llm( txt.replace("{h1}", self.get_hyphotesis_str(h1)).replace("{h2}", self.get_hyphotesis_str(h2)).replace("{subgraph}", self.subgraph_str).replace("{start_node}", self.subgraph.start_node).replace("{end_node}", self.subgraph.end_node) )
                with open(f'hackathon/prompts/{prompt2}', 'r', encoding='UTF-8') as f:
                    ans = llm(f.read())
                
                fnd = False
                digs = ""
                for i in reversed(range(len(ans))):
                    dg = ans[i] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', '-']
                    if fnd:
                        if not dg:
                            break
                        else:
                            digs += ans[i]
                    elif dg:
                        fnd = True
                        digs += ans[i]
                score += int(''.join(list(reversed(digs))))
            except Exception as e:
                print(f'COMPARATOR GOT AN ERROR: {e}')
        
        return score


    def forward(self, hypothesis: List[Hypothesis], links: List[Tuple[int, int]]) -> np.array:
        # computes matrix (len(hypothesis), len(hypothesis)) that computes scores for each pair of nodes in links and -inf everywhere else
        # forward(["a", "b", "c"], set([0, 1], [0, 2], [1, 2])) -> ((x, x, x), (x, x, x), (x, x, x))
        # mat[i, j] = 1  ->  i wygrało

        mat = np.full((len(hypothesis), len(hypothesis)), float("-inf"))
        for i in range(len(hypothesis)):
            mat[i, i] = 0
        lock = threading.Lock()

        def compute_score(i, j):
            score = self.compare(hypothesis[i], hypothesis[j])
            with lock:
                if mat[i, j] == float("-inf"):
                    mat[i, j] = score
                    mat[j, i] = -score

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(compute_score, i, j) for i, j in links]
            for _ in as_completed(futures):
                pass

        return mat

