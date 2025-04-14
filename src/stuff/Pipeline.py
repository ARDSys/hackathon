import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, List

from src.stuff.agents.AbstractAgent import AbstractAgent, AgentResult
from src.stuff.PipelineStructure import PipelineStructure
from src.stuff.ResultParser import ResultParser
from src.stuff.ResultsMerger import ResultsMerger


class Pipeline:

    LOG_DIR: Path = Path.cwd() / "logs"

    def __init__(self, structure: PipelineStructure, max_iters: int = 20):
        self._actual_agent_id: int = 0
        self._actual_result: AgentResult = None
        self._max_iters = max_iters
        self.set_structure(structure)

    def set_structure(self, structure: PipelineStructure):
        self._structure = structure
        self._actual_node_id = self._structure.start

    def run(self, subgraph: Any = None) -> Any:
        self._actual_result = ResultParser.parse_subgraph(subgraph)
        iters = 0
        while not self._actual_result.stop or iters >= self._max_iters:
            self._step()
            iters += 1
        return self._actual_result

    def _get_agents(self, id: int) -> List[AbstractAgent]:
        return self._structure.nodes[id].agents
    
    def _step(self):
        agents = self._get_agents(self._actual_node_id)
        self._actual_result = ResultsMerger.merge(
            [agent.run(self._actual_result) for agent in agents]
        )
        self._log_result()
        self._actual_node_id = self._structure.edges[self._actual_node_id].output
    
    def _log_result(self):
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.LOG_DIR / f"log_{time.time()}.json", "w") as f:
            json.dump(asdict(self._actual_result), f, indent=4)

