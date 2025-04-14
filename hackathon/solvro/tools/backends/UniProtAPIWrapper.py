import os
import time
import random
import requests
from typing import Optional

class UniProtAPIWrapper:
    def __init__(self, max_retry: int = 3, sleep_time: float = 1.0):
        self.base_url = "https://rest.uniprot.org/uniprotkb/search"
        self.max_retry = max_retry
        self.sleep_time = sleep_time

    def search(self, query: str) -> Optional[dict]:
        search_params = {
            "query": query,
            "format": "json",
            "fields": "accession",
            "size": 1
        }

        retry = 0
        while retry <= self.max_retry:
            try:
                search_response = requests.get(self.base_url, params=search_params, timeout=10)
                search_response.raise_for_status()
                search_data = search_response.json()
                if not search_data.get("results"):
                    return None

                accession = search_data["results"][0]["primaryAccession"]

                # Step 2: Fetch full entry by accession
                entry_url = f"https://rest.uniprot.org/uniprotkb/{accession}.json"
                entry_response = requests.get(entry_url, timeout=10)
                entry_response.raise_for_status()
                return entry_response.json()

            except requests.exceptions.HTTPError as e:
                if search_response.status_code == 429 and retry < self.max_retry:
                    sleep_time = self.sleep_time * (2 ** retry) + random.uniform(0.5, 1.5)
                    print(f"Rate limited. Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    retry += 1
                else:
                    print(f"HTTP error occurred: {e}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"Request exception: {e}")
                return None

            retry = 0
            while retry <= self.max_retry:
                try:
                    response = requests.get(self.base_url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    if data.get("results"):
                        return data["results"][0]
                    else:
                        return None
                except requests.exceptions.HTTPError as e:
                    if response.status_code == 429 and retry < self.max_retry:
                        sleep_time = self.sleep_time * (2 ** retry) + random.uniform(0.5, 1.5)
                        print(f"Rate limited. Retrying in {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
                        retry += 1
                    else:
                        print(f"HTTP error occurred: {e}")
                        return None
                except requests.exceptions.RequestException as e:
                    print(f"Request exception: {e}")
                    return None
            return None
