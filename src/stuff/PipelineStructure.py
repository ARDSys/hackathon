from dataclasses import dataclass
from typing import Dict, List

from src.stuff.agents.AbstractAgent import AbstractAgent


@dataclass
class Node:
    agents: List[AbstractAgent]


@dataclass
class Edge:
    output: int


@dataclass
class PipelineStructure:
    start: int
    nodes: Dict[int, Node]  # {id: Node}
    edges: Dict[int, Edge]  # {input: Edge}
