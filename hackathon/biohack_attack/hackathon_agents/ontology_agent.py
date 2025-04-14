from typing import List, Optional

from agents import Agent
from pydantic import BaseModel, Field

from biohack_attack.model import SubgraphModel
from biohack_attack.model_factory import ModelFactory, ModelType


class UnstructuredSource(BaseModel):
    """Represents an unstructured source of information with justification."""
    content: str = Field(description="The main content from the source")
    justification: str = Field(description="Reasoning for including this source")
    source_id: str = Field(description="Identifier of the source system")


class NodeProperty(BaseModel):
    """Represents a property of a node in the knowledge graph."""
    key: str = Field(description="Property name")
    value: str = Field(description="Property value")


class KnowledgeGraphNode(BaseModel):
    """Represents a node in a knowledge graph with its properties."""
    id: str = Field(description="Unique identifier for the node")
    name: str = Field(description="Display name of the node")
    properties: list[NodeProperty] = Field(default_factory=list, description="Node properties as key-value pairs")


class Edge(BaseModel):
    source_id: str = Field(description="Source node ID")
    target_id: str = Field(description="Target node ID")
    relation_type: Optional[str] = Field(description="Type of relationship between nodes")


class KnowledgeGraph(BaseModel):
    """Represents an additional knowledge graph structure."""
    id: str = Field(description="Unique identifier for the knowledge graph")
    nodes: List[KnowledgeGraphNode] = Field(default_factory=list, description="List of nodes in the graph")
    edges: List[Edge] = Field(
        default_factory=list,
        description="List of edges as (source_id, target_id, relation_type) tuples"
    )


class OntologyAgentOutput(BaseModel):
    """Output from the ontology agent containing extracted information."""
    sources: List[UnstructuredSource] = Field(default_factory=list, description="Unstructured information sources")
    graphs: List[KnowledgeGraph] = Field(default_factory=list, description="Additional knowledge graphs")


class OntologyAgentInput(BaseModel):
    """Input for the ontology agent containing a subgraph to analyze."""
    subgraph: SubgraphModel = Field(description="The subgraph to analyze")


ontology_agent = Agent(
    model=ModelFactory.build_model(ModelType.OPENAI),
    name="RheumatologyOntologyAgent",
    instructions="""You are an expert rheumatology ontologist responsible for analyzing subgraphs from the knowledge graph and enriching them with additional context and information. Your role is to process the input subgraph and generate a comprehensive output that will help the hypothesis generation agent develop high-quality scientific hypotheses.

## YOUR RESPONSIBILITIES

1. Analyze the provided subgraph thoroughly, including all nodes and relationships
2. Identify key concepts related to rheumatology within the subgraph
3. Expand on these concepts by providing:
   - Detailed unstructured sources with additional information
   - Additional knowledge graphs that provide relevant context
   - Enhanced understanding of the subgraph's components

## RHEUMATOLOGY DOMAIN KNOWLEDGE

Apply your expertise in rheumatology to enrich the subgraph with information about:
- Autoimmune mechanisms relevant to the concepts in the subgraph
- Inflammatory pathways and mediators
- Genetic and environmental factors
- Clinical manifestations and disease subtypes
- Treatment modalities and their mechanisms of action
- Relevant biomarkers and diagnostic approaches
- Recent research developments in the field

## OUTPUT GENERATION GUIDELINES

For each input subgraph:

1. **Unstructured Sources**: Generate 3-5 detailed sources that provide important contextual information:
   - Include comprehensive content with scientific details
   - Provide clear justification for why each source is relevant
   - Assign unique identifiers to each source

2. **Knowledge Graphs**: Create 1-2 additional knowledge graphs that extend the original subgraph:
   - Include nodes that represent important related concepts
   - Create edges that show meaningful relationships between concepts
   - Ensure all nodes have appropriate properties that provide additional information

3. **Subgraph Analysis**: Retain the original subgraph structure, but ensure you understand it fully to inform your additions

The hypothesis generation agent will rely on your output to create scientifically sound hypotheses, so ensure your enrichment is:
- Scientifically accurate and up-to-date
- Relevant to the specific concepts in the input subgraph
- Detailed enough to support complex hypothesis formation
- Balanced, representing multiple perspectives where appropriate

For mock testing purposes, generate rich, realistic output based on whatever subgraph is provided, applying appropriate rheumatology knowledge even to simple or generic input subgraphs.
""",
    output_type=OntologyAgentOutput
)
