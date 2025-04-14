import os

import pandas as pd
from agents import function_tool

EDGE_TYPE_MAPPING = {
    "AdG": "Anatomy downregulates Gene",
    "AeG": "Anatomy expresses Gene",
    "AuG": "Anatomy upregulates Gene",
    "CbG": "Compound binds Gene",
    "CcSE": "Compound causes Side Effect",
    "CdG": "Compound downregulates Gene",
    "CpD": "Compound palliates Disease",
    "CrC": "Compound resembles Compound",
    "CtD": "Compound treats Disease",
    "CuG": "Compound upregulates Gene",
    "DaG": "Disease associates Gene",
    "DdG": "Disease downregulates Gene",
    "DlA": "Disease localizes Anatomy",
    "DpS": "Disease presents Symptom",
    "DrD": "Disease resembles Disease",
    "DuG": "Disease upregulates Gene",
    "GcG": "Gene covaries Gene",
    "GiG": "Gene interacts Gene",
    "GpBP": "Gene participates Biological Process",
    "GpCC": "Gene participates Cellular Component",
    "GpMF": "Gene participates Molecular Function",
    "GpPW": "Gene participates Pathway",
    "Gr>G": "Gene regulates Gene",
    "PCiC": "Pharmacologic Class includes Compound",
}


@function_tool()
async def query_hetionet(keyword: str):
    """
    Query the Hetionet database for a given keyword. Returns a string representation of one-hop relationships.
    
    Hetionet is a heterogeneous network of biomedical knowledge that integrates data from various sources.
    It contains different types of nodes (Anatomy, Compound, Disease, Gene, etc.) and edges representing 
    relationships between them (e.g., 'Compound treats Disease', 'Disease associates Gene').
    The network helps discover patterns and generate hypotheses in biomedical research.

    Args:
        keyword (str): The keyword to search for in node names. Can be a disease, gene, compound, etc.

    Returns:
        str: A string containing the matched node information and all its immediate relationships,
             including the type of relationship and connected node details. Returns an error message
             if no matches are found or if the query fails.
    """
    df_nodes, df_edges = load_hetionet()

    try:
        # Find matching nodes
        # Remove special characters from keyword and node names for fuzzy matching
        clean_keyword = "".join(e for e in keyword if e.isalnum())

        matching_nodes = df_nodes[
            (df_nodes["name"].str.contains(keyword, case=False, na=False))
            | (
                df_nodes["name"]
                .str.replace(r"[^a-zA-Z0-9]", "")
                .str.contains(clean_keyword, case=False, na=False)
            )
        ]

        if matching_nodes.empty:
            return f"No nodes found matching keyword: {keyword}"

        result = []
        for _, node in matching_nodes.iterrows():
            node_id = node["id"]
            result.append(f"Node: {node['name']} (Type: {node['kind']})")

            # Find edges where this node is either source or target
            related_edges = df_edges[
                (df_edges["source_id"] == node_id) | (df_edges["target_id"] == node_id)
            ]

            for _, edge in related_edges.iterrows():
                source_node = df_nodes[df_nodes["id"] == edge["source_id"]].iloc[0]
                target_node = df_nodes[df_nodes["id"] == edge["target_id"]].iloc[0]

                edge_type = EDGE_TYPE_MAPPING.get(edge["kind"], edge["kind"])

                if source_node["id"] == node_id:
                    result.append(
                        f"  -> {edge_type} -> {target_node['name']} (Type: {target_node['kind']})"
                    )
                else:
                    result.append(
                        f"  <- {edge_type} <- {source_node['name']} (Type: {source_node['kind']})"
                    )

        return "\n".join(result)

    except Exception as e:
        return f"Error querying Hetionet: {str(e)}"


def load_hetionet():
    """
    Loads the Hetionet dataset from local files and returns it as a NetworkX graph.

    Returns:
        nx.Graph: A NetworkX graph representation of Hetionet
        dict: A dictionary containing node metadata
    """
    # Get the directory of the current script
    current_dir = ""

    # Paths to local files
    edges_path = os.path.join(
        current_dir, "data", "hetionet", "hetionet-v1.0-edges.sif"
    )
    nodes_path = os.path.join(
        current_dir, "data", "hetionet", "hetionet-v1.0-nodes.tsv"
    )

    # Load edges from SIF file
    df_edges = pd.read_csv(
        edges_path, sep="\t", header=None, names=["source_id", "kind", "target_id"]
    )

    df_nodes = pd.read_csv(nodes_path, sep="\t")

    return df_nodes, df_edges
