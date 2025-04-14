from DisGeNETAPIWrapper import DisGeNETAPIWrapper
from pubmed import PubMedAPIWrapperImproved
from dotenv import load_dotenv
import os
import json

def gene_to_pubmed_context(
    gene_symbol: str,
    gene_ncbi_id: str,
    disgenet_wrapper,
    pubmed_wrapper,
    max_diseases: int = 5,
    max_articles: int = 3,
) -> dict:
    result = {
        "gene": gene_symbol,
        "diseases": []
    }

    # Step 1: Get gene-disease associations
    disgenet_data = disgenet_wrapper.search_by_gene_ncbi_id(gene_ncbi_id)
    if not disgenet_data:
        print("❌ No DisGeNET data found.")
        return result

    payload = disgenet_data.get("payload", [])[:max_diseases]

    for disease in payload:
        disease_name = disease.get("diseaseName")
        disease_cui = disease.get("diseaseUMLSCUI")
        score = disease.get("score")

        # Step 2: Formulate PubMed query
        pubmed_query = f"{gene_symbol} AND \"{disease_name}\""
        articles = pubmed_wrapper.run(pubmed_query)

        # Step 3: Structure disease entry
        disease_entry = {
            "name": disease_name,
            "cui": disease_cui,
            "score": score,
            "pubmed_query": pubmed_query,
            "pubmed_articles": articles[:max_articles] if isinstance(articles, list) else []
        }

        result["diseases"].append(disease_entry)

    return result

# Example usage
if __name__ == "__main__":
    load_dotenv()
    disgenet_token = os.getenv("DISGENET_API_KEY")
    pubmed_token = os.getenv("PUBMED_API_KEY")
    print(f"PubMed API key: {pubmed_token}")

    disgenet = DisGeNETAPIWrapper(api_key=disgenet_token)
    pubmed = PubMedAPIWrapperImproved(api_key=pubmed_token)

    context = gene_to_pubmed_context(
        gene_symbol="PTPN22",
        gene_ncbi_id="5781",
        disgenet_wrapper=disgenet,
        pubmed_wrapper=pubmed,
        max_diseases=3,
        max_articles=2
    )
    print(json.dumps(context, indent=2))