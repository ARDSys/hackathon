from langchain.tools import BaseTool
from typing import Optional
from .UniProtAPIWrapper import UniProtAPIWrapper
from langchain.tools import BaseTool
from typing import Optional
from pydantic import Field

class UniProtQueryTool(BaseTool):
    name: str = Field(default="uniprot_query", description="The name of the tool.")
    description: str = Field(default="Searches UniProt for protein or gene information.")
    api_wrapper: UniProtAPIWrapper

    def _run(self, query: str) -> Optional[dict]:
        return self.api_wrapper.search(query)

    async def _arun(self, query: str) -> Optional[dict]:
        raise NotImplementedError("Async not implemented.")
    
def parse_uniprot_entry(data: dict) -> dict:
    """Extracts relevant fields from UniProt entry JSON into a clean dict."""
    result = {}

    # Basic identifiers
    result["accession"] = data.get("primaryAccession", "")
    result["protein_id"] = data.get("uniProtkbId", "")

    # Organism
    result["organism"] = data.get("organism", {}).get("scientificName", "")

    # Protein name
    result["protein_name"] = (
        data.get("proteinDescription", {})
            .get("recommendedName", {})
            .get("fullName", {})
            .get("value", "")
    )

    #cross references
    result["cross_references"] = extract_cross_references(
    data,
    databases=["EMBL", "Ensembl", "HGNC", "GeneID", "PDB"]
    )

    # Gene names (official + synonyms)
    gene_names = []
    for gene in data.get("genes", []):
        name = gene.get("geneName", {}).get("value")
        if name:
            gene_names.append(name)
        for syn in gene.get("synonyms", []):
            syn_name = syn.get("value")
            if syn_name:
                gene_names.append(syn_name)
    result["gene_names"] = list(set(gene_names))  # deduplicate

    # Function comment
    function_texts = []
    for comment in data.get("comments", []):
        if comment.get("commentType") == "FUNCTION":
            for txt in comment.get("texts", []):
                function_texts.append(txt.get("value"))
    result["function"] = " ".join(function_texts).strip()

    # Subcellular location
    subcellular_locs = []
    for comment in data.get("comments", []):
        if comment.get("commentType") == "SUBCELLULAR LOCATION":
            for location in comment.get("subcellularLocations", []):
                loc = location.get("location", {}).get("value")
                if loc:
                    subcellular_locs.append(loc)
    result["subcellular_location"] = list(set(subcellular_locs))

    # Associated diseases (commentType: "DISEASE")
    diseases = []
    for comment in data.get("comments", []):
        if comment.get("commentType") == "DISEASE":
            disease = comment.get("disease", {}).get("diseaseId")
            if disease:
                diseases.append(disease)
    result["associated_diseases"] = diseases

    # Keywords
    result["keywords"] = [kw["value"] for kw in data.get("keywords", []) if "value" in kw]

    return result

def extract_cross_references(data: dict, databases: list[str] = None) -> dict:
    """
    Extracts a subset of useful cross-references from UniProt entry.
    """
    refs = {}
    for entry in data.get("uniProtKBCrossReferences", []):
        db = entry.get("database")
        if databases and db not in databases:
            continue
        ref_id = entry.get("id")
        props = {prop["key"]: prop["value"] for prop in entry.get("properties", []) if "key" in prop and "value" in prop}
        if db not in refs:
            refs[db] = []
        refs[db].append({
            "id": ref_id,
            "properties": props
        })
    return refs


# if __name__ == "__main__":
#     uniprot_wrapper = UniProtAPIWrapper()
#     uniprot_tool = UniProtQueryTool(api_wrapper=uniprot_wrapper)

#     test_query = "BRCA1"  # You can replace this with any protein or gene name
#     print(f"Querying UniProt for: {test_query}")
#     result = uniprot_tool.run(test_query)

#     # if result:
#     #     print("✅ Result:")
#     #     for k, v in result.items():
#     #         print(f"{k}: {v}")
#     # else:
#     #     print("❌ No results found.")
    
#     # raw_entry = api_wrapper.search("BRCA1")
#     parsed_entry = parse_uniprot_entry(result)
#     print(parsed_entry)

