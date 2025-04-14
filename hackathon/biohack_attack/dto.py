from typing import Optional

from pydantic import BaseModel

from biohack_attack.hackathon_agents.critic_agent import TriagedHypothesis
from biohack_attack.hackathon_agents.decomposition_agent import HypothesisDecomposition
from biohack_attack.hackathon_agents.hypothesis_agent import ScientificHypothesis
from biohack_attack.hackathon_agents.ontology_agent import OntologyAgentOutput
from biohack_attack.hackathon_agents.verification_agent import HypothesisVerification
from biohack_attack.model import SubgraphModel


class ProcessedHypothesis(BaseModel):
    iteration: int
    base_hypothesis: ScientificHypothesis
    triaged_hypothesis: Optional[TriagedHypothesis] = None
    decomposed_hypothesis: Optional[HypothesisDecomposition] = None
    hypothesis_assessment: Optional[HypothesisVerification] = None
    score: Optional[float] = None


class HypothesisGenerationDTO(BaseModel):
    subgraph_model: SubgraphModel
    ontology: Optional[OntologyAgentOutput] = None
    hypotheses: list[list[ProcessedHypothesis]] = []
    current_iteration: int = 0
    best_hypothesis_id: Optional[str] = None
