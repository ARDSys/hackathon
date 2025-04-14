from pydantic import BaseModel, Field
from enum import Enum

from typing import List, Union


class DataSource(Enum):
    BIORXIV = "biorxiv"
    EUROPE_PMC = "europe pmc"
    HETIONET = "hetionet"
    PUBMED = "pubmed"
    SEMANTIC_SCHOLAR = "semantic scholar"
    FIRECRAWL = "firecrawl"


class Query(BaseModel):
    reasoning: str
    data_source: DataSource
    keyword: str


class QueriesOutput(BaseModel):
    reasoning: str
    queries: List[Query]


class Triple(BaseModel):
    """
    Represents a semantic triple in a knowledge graph, consisting of subject, predicate, and object.

    A triple is the fundamental unit of knowledge representation in RDF (Resource Description Framework)
    and similar knowledge graph structures, expressing a relationship between two entities.
    """

    subject: str = Field(
        description="The entity that is being described or acting (the source node in the graph)"
    )
    predicate: str = Field(
        description="The property or relationship that connects the subject to the object"
    )
    object: str = Field(
        description="The entity, value, or target that the subject relates to (the target node in the graph)"
    )


class KnowledgeGraph(BaseModel):
    """
    Represents a knowledge graph structure composed of semantic triples.

    A knowledge graph is a network of entities, their properties, and the relationships between them.
    It organizes information in a graph structure where nodes represent entities and edges represent relationships.
    """

    triples: List[Triple] = Field(
        default_factory=list,
        description="Collection of semantic triples that form the knowledge graph structure",
    )


class UnstructuredSource(BaseModel):
    """Represents an unstructured source of information with justification."""

    content: str = Field(description="The main content from the source")
    justification: str = Field(description="Reasoning for including this source")
    source_id: str = Field(description="Identifier of the source system")


class ResearchAgentOutput(BaseModel):
    """Output from the ontology agent containing extracted information."""

    sources: List[UnstructuredSource] = Field(
        default_factory=list,
        description="List of additional unstructured information sources.",
    )
    graphs: List[KnowledgeGraph] = Field(
        default_factory=list, description="List of additional Knowledge Graphs."
    )
