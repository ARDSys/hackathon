import time
import random
import requests
from typing import Optional, List
from langchain.tools import BaseTool
from pydantic import Field, SkipValidation


# === DisGeNET API Wrapper ===
class DisGeNETAPIWrapper:
    def __init__(self, api_key: str, max_retry: int = 3, sleep_time: float = 1.0):
        self.api_key = api_key
        self.base_url = "https://api.disgenet.com/api/v1/gda/summary"
        self.max_retry = max_retry
        self.sleep_time = sleep_time
        self.headers = {
            "Authorization": self.api_key,
            "accept": "application/json"
        }

    def search_by_gene_ncbi_id(self, gene_ncbi_id: str, page: int = 0) -> Optional[dict]:
        params = {
            "gene_ncbi_id": gene_ncbi_id,
            "page_number": str(page)
        }

        retry = 0
        while retry <= self.max_retry:
            response = requests.get(self.base_url, headers=self.headers, params=params)

            if response.status_code == 429:
                wait_time = int(response.headers.get("x-rate-limit-retry-after-seconds", 5))
                print(f"[DisGeNET] Rate limit hit. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                retry += 1
                continue

            if not response.ok:
                print(f"[DisGeNET] HTTP Error {response.status_code}: {response.text[:300]}")
                return None

            try:
                return response.json()
            except ValueError:
                print("[DisGeNET] Error parsing response JSON.")
                return None