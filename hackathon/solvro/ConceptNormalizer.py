from langchain_core.tools import Tool
from typing import Dict, Any, Callable

class ConceptNormalizer:
    def __init__(self, ensembl_tool, uniprot_tool, generate_id_fn: Callable[[str], str] = None):
        self.ensembl_tool = ensembl_tool
        self.uniprot_tool = uniprot_tool
        # Use a custom node ID generator if provided; otherwise use a default.
        self.generate_id_fn = generate_id_fn or (lambda term: f"node_{term}")

    def normalize(self, term: str) -> Dict[str, Any]:
        """
        Normalize a biomedical term using Ensembl and UniProt. Additionally,
        generate an identifier for integration into a knowledge graph.
        """
        result = {
            "original_term": term,
            "normalized": None,
            "type": None,
            "synonyms": [],
            "source": None,
            "node_id": self.generate_id_fn(term)  # This ID is used as a unique identifier in the KG.
        }

        # 1. Try Ensembl (gene lookup)
        try:
            ensembl_result = self.ensembl_tool.run({"gene_symbol": term})
            if ensembl_result and "ensembl_id" in ensembl_result:
                result.update({
                    "normalized": ensembl_result.get("ncbi_id", term),
                    "type": "gene",
                    "synonyms": ensembl_result.get("aliases", []),
                    "source": "Ensembl"
                })
                result["display_name"] = result["normalized"]
                return result
        except Exception:
            pass

        # 2. Try UniProt (protein lookup)
        try:
            uniprot_result = self.uniprot_tool.run({"query": term})
            if uniprot_result and "protein_name" in uniprot_result:
                result.update({
                    "normalized": uniprot_result.get("protein_name", term),
                    "type": "protein",
                    "synonyms": uniprot_result.get("gene_names", []),
                    "source": "UniProt"
                })
                result["display_name"] = result["normalized"]
                return result
        except Exception:
            pass

        # 3. Fallback to heuristic if both lookups fail
        result.update({
            "normalized": term,
            "type": "unknown",
            "source": "heuristic",
            "display_name": term
        })
        return result

    def to_kg_node(self, normalized_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts the normalized output into a structure ready for insertion as a node
        in the knowledge graph.
        """
        return {
            "id": normalized_result.get("node_id"),
            "name": normalized_result.get("normalized"),
            "type": normalized_result.get("type"),
            "aliases": normalized_result.get("synonyms"),
            "source": normalized_result.get("source"),
            "original_term": normalized_result.get("original_term")
        }

def create_concept_normalizer_tool(ensembl_tool, uniprot_tool, generate_id_fn: Callable[[str], str] = None):
    """
    Wraps the ConceptNormalizer instance as a LangChain tool.
    When invoked, it returns the normalized concept along with a knowledge graph node
    representation to be used by the agent in exploring a research topic.
    """
    normalizer = ConceptNormalizer(ensembl_tool, uniprot_tool, generate_id_fn)

    def tool_fn(input_data: Dict[str, str]) -> Dict[str, Any]:
        term = input_data.get("term", "")
        normalized_result = normalizer.normalize(term)
        # Produce a KG node representation in addition to the raw normalization.
        kg_node = normalizer.to_kg_node(normalized_result)
        normalized_result["kg_node"] = kg_node
        return normalized_result

    return Tool(
        name="ConceptNormalizer",
        description=(
            "Normalizes a free-text biomedical term to a standardized form "
            "for knowledge graph integration. Ideal for exploring a topic based "
            "on a starting KG node to generate scientific hypotheses. Returns the "
            "normalized form, type (gene/protein/unknown), synonyms, and a KG-ready node."
        ),
        args_schema={"term": str},
        func=tool_fn
    )


# --- Mock Tools for Demonstration ---

class MockEnsemblTool:
    def run(self, input_data: Dict[str, Any]):
        # Simulate that "BRCA1" returns gene data via Ensembl.
        if input_data.get("gene_symbol") == "BRCA1":
            return {
                "ensembl_id": "ENSG000001",
                "ncbi_id": "NCBI_BRCA1",
                "aliases": ["BRCA1_alias1", "BRCA1_alias2"]
            }
        return {}

class MockUniProtTool:
    def run(self, input_data: Dict[str, Any]):
        # Simulate that "TP53" returns protein data via UniProt.
        if input_data.get("query") == "TP53":
            return {
                "protein_name": "TP53_protein",
                "gene_names": ["TP53", "p53"]
            }
        return {}

# --- Demo Usage: Agent Exploration and Knowledge Graph Integration ---

def main():
    # Instantiate mock database tools.
    ensembl_tool = MockEnsemblTool()
    uniprot_tool = MockUniProtTool()

    # Create the ConceptNormalizer tool with a custom node ID generator.
    tool = create_concept_normalizer_tool(ensembl_tool, uniprot_tool, generate_id_fn=lambda term: f"kg_{term.lower()}")

    # Example 1: Starting from a known gene node ("BRCA1")
    starting_node = "BRCA1"
    normalized_data = tool.func({"term": starting_node})
    print("Normalized Data for 'BRCA1':")
    print(normalized_data)
    print("Knowledge Graph Node Representation:")
    print(normalized_data["kg_node"])

    # Example 2: Starting with a term expected to resolve as a protein ("TP53")
    protein_node = "TP53"
    normalized_data_protein = tool.func({"term": protein_node})
    print("\nNormalized Data for 'TP53':")
    print(normalized_data_protein)
    print("Knowledge Graph Node Representation:")
    print(normalized_data_protein["kg_node"])

    # Example 3: Fallback case when no database info is found (for example, an ambiguous term)
    unknown_node = "UNKNOWN_TERM"
    normalized_data_unknown = tool.func({"term": unknown_node})
    print("\nNormalized Data for 'UNKNOWN_TERM':")
    print(normalized_data_unknown)
    print("Knowledge Graph Node Representation:")
    print(normalized_data_unknown["kg_node"])


if __name__ == "__main__":
    main()