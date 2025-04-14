import math
from dataclasses import dataclass
from typing import List

from .state import HypgenState


@dataclass
class HypothesisNode:
    hypothesis: str
    visits: int = 0
    total_score: float = 0.0
    children: List['HypothesisNode'] | None = None

    @property
    def average_score(self) -> float:
        return self.total_score / self.visits if self.visits > 0 else 0

    def uct_score(self, total_visits: int, exploration_constant: float = 1.414) -> float:
        """Calculate UCT score for this hypothesis node using global total visits"""
        if self.visits == 0:
            return float('inf')
        exploitation = self.average_score
        exploration = exploration_constant * math.sqrt(math.log(total_visits) / self.visits)
        return exploitation + exploration


class HypothesisTree:
    """Class to manage the tree of hypotheses and track global statistics."""
    
    def __init__(self):
        self.root: HypothesisNode | None = None
        self.total_visits: int = 0
        self.current_node: HypothesisNode | None = None
    
    @classmethod
    def from_state(cls, state: HypgenState) -> 'HypothesisTree':
        """Create or retrieve a hypothesis tree from state."""
        tree = state.get("hypothesis_tree")
        if tree is None:
            tree = cls()
            if "hypothesis" in state:
                tree.root = HypothesisNode(hypothesis=state["hypothesis"])
                tree.current_node = tree.root
        return tree
    
    def visit_node(self, node: HypothesisNode, score: float) -> None:
        """Record a visit to a node with its score."""
        node.visits += 1
        node.total_score += score
        self.total_visits += 1
    
    def add_child(self, parent: HypothesisNode, hypothesis: str) -> HypothesisNode:
        """Add a new hypothesis as a child of the given node."""
        if parent.children is None:
            parent.children = []
        
        child = HypothesisNode(hypothesis=hypothesis)
        parent.children.append(child)
        return child

    def select_best_child(self, node: HypothesisNode, exploration_constant: float = 1.414) -> HypothesisNode | None:
        """Select the child node with the highest UCT score"""
        if not node.children:
            return None
        
        return max(node.children, key=lambda child: child.uct_score(self.total_visits, exploration_constant))