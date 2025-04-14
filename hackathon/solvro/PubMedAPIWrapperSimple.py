# === Simplified PubMed Wrapper ===
from typing import Any, Dict, List
import requests


class PubMedAPIWrapperSimple:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    def run(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results,
            "api_key": self.api_key
        }
        search_response = requests.get(self.base_url, params=params)
        if not search_response.ok:
            print(f"[PubMed] Error: {search_response.status_code}")
            return []

        ids = search_response.json().get("esearchresult", {}).get("idlist", [])
        return [{"pmid": pmid} for pmid in ids]