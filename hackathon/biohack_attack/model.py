from typing import Dict, List, Optional, Any, Type

from pydantic import BaseModel, Field

from ard.subgraph import Subgraph


# Define a function to create a clean schema
def create_clean_schema(model_class: Type[BaseModel]) -> dict:
    """Create a JSON schema without additionalProperties fields."""
    schema = model_class.model_json_schema()

    # Function to recursively remove additionalProperties
    def clean_schema(schema_part):
        if not isinstance(schema_part, dict):
            return schema_part

        # Remove additionalProperties
        if 'additionalProperties' in schema_part:
            del schema_part['additionalProperties']

        # Process nested structures
        for key, value in list(schema_part.items()):
            if isinstance(value, dict):
                schema_part[key] = clean_schema(value)
            elif isinstance(value, list):
                schema_part[key] = [clean_schema(item) if isinstance(item, dict) else item for item in value]

        return schema_part

    # Clean the schema
    return clean_schema(schema)


class Relation(BaseModel):
    relation: str
    triplet_id: int


class NodeData(BaseModel):
    sources: List[Relation]
    node_name: str


class EdgeData(BaseModel):
    source: str
    target: str
    relation: str
    sources: List[Relation]


class GraphData(BaseModel):
    """Representation of the graph structure with nodes and edges."""
    nodes: list[NodeData] = Field(
        description="Dictionary mapping node names to their attributes"
    )
    edges: List[EdgeData] = Field(
        default_factory=list,
        description="List of edge dictionaries with source, target, and attributes"
    )


class GraphStats(BaseModel):
    """Statistics about the graph structure."""
    node_count: int = Field(description="Number of nodes in the graph")
    edge_count: int = Field(description="Number of edges in the graph")
    path_length: int = Field(description="Length of the path from start to end node")


class GraphMetadata(BaseModel):
    """Metadata about the original graph."""
    node_count: int = Field(description="Number of nodes in the original graph")
    edge_count: int = Field(description="Number of edges in the original graph")


class PathEdge(BaseModel):
    """Representation of an edge in the path."""
    source: str = Field(description="Source node of the edge")
    target: str = Field(description="Target node of the edge")
    relation: str = Field(default="", description="Relationship type between nodes")


class SubgraphModel(BaseModel):
    """Pydantic model representing a Subgraph."""
    subgraph_id: str = Field(description="Unique identifier for the subgraph")
    graph_data: GraphData = Field(description="The graph structure data")
    graph_stats: GraphStats = Field(description="Statistics about the graph")
    start_node: str = Field(description="The starting node of the path")
    end_node: str = Field(description="The ending node of the path")
    path_nodes: List[str] = Field(description="The ordered list of nodes in the path")
    path_edges: List[PathEdge] = Field(description="The edges connecting nodes in the path")
    context: Optional[str] = Field(None, description="Analysis context generated for the subgraph")
    path_score: Optional[int] = Field(None, description="Score assigned to the path (1-5)")
    path_score_justification: Optional[str] = Field(None, description="Justification for the path score")
    original_graph_metadata: GraphMetadata = Field(description="Metadata about the original graph")

    # Override the model_json_schema method to use our custom schema generator
    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        return create_clean_schema(cls)

    @classmethod
    def from_subgraph(cls, subgraph: Subgraph) -> "SubgraphModel":
        """Convert a Subgraph instance to a SubgraphModel."""
        # Use the subgraph's to_json method to get serializable data
        new_nodes = []
        data = subgraph.to_json()
        for node_name, node in data["graph_data"]["nodes"].items():
            new_node = {"node_name": node_name} | node
            new_nodes.append(new_node)
        data["graph_data"]["nodes"] = new_nodes
        return cls(**data)

    def to_subgraph(self) -> Any:
        """Convert the model back to a Subgraph instance (requires implementation)."""
        # Import and use Subgraph.load_from_file with in-memory data
        from ard.subgraph import Subgraph
        import tempfile
        import json
        import os

        # Create a temporary file to store the JSON data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            json.dump(self.model_dump(), tmp)
            tmp_path = tmp.name

        try:
            # Load the subgraph from the temporary file
            subgraph = Subgraph.load_from_file(tmp_path)
            return subgraph
        finally:
            # Clean up the temporary file
            os.unlink(tmp_path)
