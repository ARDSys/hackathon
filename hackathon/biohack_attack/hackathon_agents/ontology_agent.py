from typing import List, Optional

from agents import Agent, ModelSettings
from pydantic import BaseModel, Field

from biohack_attack.model import SubgraphModel
from biohack_attack.model_factory import ModelFactory, ModelType
from biohack_attack.tools.firecrawl_tool import query_firecrawl
from biohack_attack.tools.search_api_tools import (
    get_pubmed_papers_by_keyword,
    get_semanticscholar_papers_by_keyword,
    get_biorxiv_papers_by_category,
    get_europe_pmc_papers_by_keyword,
)


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
    properties: list[NodeProperty] = Field(
        default_factory=list, description="Node properties as key-value pairs"
    )


class Edge(BaseModel):
    source_id: str = Field(description="Source node ID")
    target_id: str = Field(description="Target node ID")
    relation_type: Optional[str] = Field(
        description="Type of relationship between nodes"
    )


class KnowledgeGraph(BaseModel):
    """Represents an additional knowledge graph structure."""

    id: str = Field(description="Unique identifier for the knowledge graph")
    nodes: List[KnowledgeGraphNode] = Field(
        default_factory=list, description="List of nodes in the graph"
    )
    edges: List[Edge] = Field(
        default_factory=list,
        description="List of edges as (source_id, target_id, relation_type) tuples",
    )


class OntologyAgentOutput(BaseModel):
    """Output from the ontology agent containing extracted information."""

    sources: List[UnstructuredSource] = Field(
        default_factory=list, description="Unstructured information sources"
    )
    graphs: List[KnowledgeGraph] = Field(
        default_factory=list, description="Additional knowledge graphs"
    )


class OntologyAgentInput(BaseModel):
    """Input for the ontology agent containing a subgraph to analyze."""

    subgraph: SubgraphModel = Field(description="The subgraph to analyze")


ontology_agent = Agent(
    model=ModelFactory.build_model(ModelType.OPENAI),
    name="RheumatologyOntologyAgent",
    instructions="""You are an expert rheumatology ontologist responsible for analyzing subgraphs from the knowledge graph and enriching them with additional context and information. Your role is to process the input subgraph and generate a comprehensive output that will help the hypothesis generation agent develop high-quality scientific hypotheses.

## YOUR SEARCH STRATEGY

1. Analyze the subgraph to identify key entities and relationships that require further enrichment
2. For each key entity or relationship:
   - Formulate precise search queries based on entity names and relationships
   - Select the most appropriate search tool based on the information needed:
     * Use PubMed (get_pubmed_papers_by_keyword) for peer-reviewed medical literature
     * Use Semantic Scholar (get_semanticscholar_papers_by_keyword) for cross-disciplinary research
     * Use BioRxiv (get_biorxiv_papers_by_category) for recent preprints
     * Use Europe PMC (get_europe_pmc_papers_by_keyword) for additional biomedical literature
     * Use Firecrawl (query_firecrawl) when needing to search across multiple scientific resources
     * IMPORTANT: Don't use all tools for every entity - select 1-2 most relevant tools per entity

3. When using search tools:
   - Use specific, targeted keywords with Boolean operators (AND, OR, NOT)
   - Include synonyms for key terms to expand relevant results
   - Add "rheumatology" or specific rheumatic conditions when applicable
   - Limit searches to recent publications (last 5 years) when appropriate

## CONTENT EXTRACTION GUIDELINES

When reviewing search results:
1. Focus on extracting mechanistic relationships, not just associations
2. Prioritize information about molecular pathways, cellular processes, and clinical correlations
3. Look for conflicting or complementary evidence across different sources
4. Pay attention to methodological details that could impact the validity of findings

## OUTPUT GENERATION GUIDELINES

For each input subgraph:

1. **Unstructured Sources**: Generate 3-5 detailed sources that provide important contextual information:
   - Write comprehensive content summaries including specific scientific details
   - Extract quantitative data when available (e.g., effect sizes, p-values, confidence intervals)
   - Clearly explain the relevance to the subgraph's key entities and relationships
   - Assign unique identifiers to each source (e.g., "SOURCE_1", "SOURCE_2")

2. **Knowledge Graphs**: Create 1-2 additional knowledge graphs that extend the original subgraph:
   - Focus on adding mechanistic connections between entities
   - Ensure new nodes and edges accurately represent validated scientific knowledge
   - Add detailed properties to nodes that provide clinically relevant information

## RHEUMATOLOGY DOMAIN FOCUS

Focus your searches and enrichment on these key aspects of rheumatology:
- Autoimmune mechanisms (e.g., T-cell activation, B-cell responses, autoantibody production)
- Inflammatory pathways (e.g., cytokine signaling, NFkB activation, JAK-STAT pathways)
- Genetic associations (e.g., HLA types, SNPs, gene expression patterns)
- Environmental triggers (e.g., infections, microbiome alterations, environmental exposures)
- Disease phenotypes (e.g., joint manifestations, extra-articular features, clinical subtypes)
- Treatment mechanisms (e.g., immunomodulation, cytokine inhibition, JAK inhibitors)

The hypothesis generation agent will rely on your output to create scientifically sound hypotheses, so ensure your enrichment is scientifically accurate, current, relevant, and sufficiently detailed to support complex hypothesis formation.
""",
    output_type=OntologyAgentOutput,
    tools=[
        query_firecrawl,
        # get_pubmed_papers_by_keyword,
        get_semanticscholar_papers_by_keyword,
        # get_biorxiv_papers_by_category,
        get_europe_pmc_papers_by_keyword,
    ],
    model_settings=ModelSettings(
        tool_choice="required",
    ),
)
