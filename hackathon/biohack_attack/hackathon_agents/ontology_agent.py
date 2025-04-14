from typing import Dict, List, Tuple, Optional

from pydantic import BaseModel, Field

from biohack_attack.model import SubgraphModel


class UnstructuredSource(BaseModel):
    """Represents an unstructured source of information with justification."""
    content: str = Field(description="The main content from the source")
    justification: str = Field(description="Reasoning for including this source")
    source_id: str = Field(description="Identifier of the source system")


class KnowledgeGraphNode(BaseModel):
    """Represents a node in a knowledge graph with its properties."""
    id: str = Field(description="Unique identifier for the node")
    name: str = Field(description="Display name of the node")
    properties: Dict[str, str] = Field(default_factory=dict, description="Node properties as key-value pairs")


class KnowledgeGraph(BaseModel):
    """Represents an additional knowledge graph structure."""
    id: str = Field(description="Unique identifier for the knowledge graph")
    nodes: List[KnowledgeGraphNode] = Field(default_factory=list, description="List of nodes in the graph")
    edges: List[Tuple[str, str, Optional[str]]] = Field(
        default_factory=list,
        description="List of edges as (source_id, target_id, relation_type) tuples"
    )


class OntologyAgentOutput(BaseModel):
    """Output from the ontology agent containing extracted information."""
    sources: List[UnstructuredSource] = Field(default_factory=list, description="Unstructured information sources")
    graphs: List[KnowledgeGraph] = Field(default_factory=list, description="Additional knowledge graphs")
    subgraph: SubgraphModel = Field(description="The subgraph analyzed by the agent")


class OntologyAgentInput(BaseModel):
    """Input for the ontology agent containing a subgraph to analyze."""
    subgraph: SubgraphModel = Field(description="The subgraph to analyze")
