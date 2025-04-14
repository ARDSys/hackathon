import requests
import json
import logging
import os
import re
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
# *** UPDATED Configuration ***
PAPERS_LIMIT = 50 # Request up to 50 papers
# Fields to request: Title, Abstract, Full Author Info, Venue, Year, Citations
PAPER_FIELDS = "paperId,title,abstract,authors.authorId,authors.name,venue,year,citationCount,url,externalIds"
MAX_RETRIES = 10
RETRY_DELAY_SECONDS = 3
API_TIMEOUT = 90 # Longer timeout

# --- (Module ABC Definition remains the same) ---
class Module(ABC):
    def __init__(self): super().__init__()
    @abstractmethod
    def forward(self, *args, **kwargs) -> Any: pass
    def __call__(self, *args, **kwargs) -> Any: return self.forward(*args, **kwargs)


class SemanticScholarPaperFinder(Module): # Renamed for clarity
    """
    Takes a query string, finds relevant papers using Semantic Scholar API
    (requesting comprehensive fields), and returns the raw list of paper data.
    Includes retry logic. Does not perform filtering or saving.
    """
    def __init__(self,
                 api_key: Optional[str] = None,
                 api_url: str = SEMANTIC_SCHOLAR_API_URL,
                 papers_limit: int = PAPERS_LIMIT,
                 paper_fields: str = PAPER_FIELDS, # Use comprehensive fields
                 timeout: int = API_TIMEOUT):
        """
        Initializes the finder. Needs Semantic Scholar API Key either passed
        or set in SEMANTIC_SCHOLAR_API_KEY environment variable.
        """
        super().__init__()
        self.api_key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        self.api_url = api_url
        self.papers_limit = papers_limit
        self.paper_fields = paper_fields # Store comprehensive fields
        self.timeout = timeout
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"x-api-key": self.api_key})
            logging.info("SemanticScholarPaperFinder initialized with API key.")
        else:
            logging.warning("SemanticScholarPaperFinder initialized WITHOUT API key.")
        logging.info(f"API URL: {self.api_url}, Limit: {self.papers_limit}, Fields Requested: '{self.paper_fields}'")


    def _call_semantic_scholar_api(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Calls Semantic Scholar Paper Search API with retries."""
        if not query:
             logging.error("Cannot query API with an empty query string.")
             return None
        params = {
            "query": query,
            "limit": self.papers_limit,
            "fields": self.paper_fields
        }
        logging.info(f"Querying Semantic Scholar API with query='{query}' (limit={self.papers_limit})...")
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(self.api_url, params=params, timeout=self.timeout)
                is_retryable = response.status_code == 429 or response.status_code >= 500
                response.raise_for_status() # Check for 4xx/5xx errors
                response_json = response.json()
                papers_data = response_json.get("data", [])
                total_found = response_json.get("total", len(papers_data))
                logging.info(f"API attempt {attempt + 1} returned {len(papers_data)} papers (~{total_found} total).")
                if not isinstance(papers_data, list): logging.error("API 'data' not list"); return None
                return papers_data # Return the raw list of paper dicts

            # ...(Exception handling with retry logic remains the same)...
            except requests.exceptions.Timeout as e: logging.warning(f"Attempt {attempt + 1}/{MAX_RETRIES}: Timeout."); last_exception = e; is_retryable = True
            except requests.exceptions.HTTPError as e: logging.warning(f"Attempt {attempt + 1}/{MAX_RETRIES}: HTTP Error {e.response.status_code}."); last_exception = e
            except requests.exceptions.RequestException as e: logging.warning(f"Attempt {attempt + 1}/{MAX_RETRIES}: Request failed: {e}"); last_exception = e; is_retryable = True
            except json.JSONDecodeError as e: logging.warning(f"Attempt {attempt + 1}/{MAX_RETRIES}: JSON Decode Error."); last_exception = e; is_retryable = True
            except Exception as e: logging.exception(f"Attempt {attempt + 1}/{MAX_RETRIES}: Unexpected error: {e}"); last_exception = e; is_retryable = True

            if is_retryable and attempt < MAX_RETRIES - 1:
                logging.info(f"Waiting {RETRY_DELAY_SECONDS}s before next retry...")
                time.sleep(RETRY_DELAY_SECONDS)
            elif not is_retryable:
                logging.error(f"Non-retryable error received: {last_exception}")
                # Log details if possible
                try: error_details = e.response.json(); logging.error(f"API Error Details: {error_details}")
                except: pass
                break # Exit loop for non-retryable http errors

        logging.error(f"API call failed after {MAX_RETRIES} attempts for query: '{query}'.");
        if last_exception: logging.error(f"Last error: {last_exception}")
        return None # Return None if all retries fail

    def forward(self, query_string: str) -> Optional[List[Dict[str, Any]]]:
        """
        Takes a query string, queries Semantic Scholar for relevant papers,
        and returns the list of paper dictionaries.

        Args:
            query_string: The string to use for the Semantic Scholar keyword search.

        Returns:
            A list of paper dictionaries (with fields as requested), or None on failure.
        """
        if not query_string or not isinstance(query_string, str):
            logging.error("Invalid query_string provided to forward method.")
            return None

        # Use the input string directly as the search query
        search_query = query_string.strip()
        logging.info(f"Using query string for search: '{search_query}'")

        # Call API (with retries handled internally)
        papers_data = self._call_semantic_scholar_api(search_query)

        if papers_data is None:
            logging.error(f"Failed to retrieve papers for query: '{search_query}'")
            return None # API call ultimately failed

        # Return the raw list (no filtering or saving within this class)
        return papers_data


# --- Example Usage ---
if __name__ == "__main__":
    # !!! IMPORTANT: Provide your Semantic Scholar API Key !!!
    # Set environment variable SEMANTIC_SCHOLAR_API_KEY OR uncomment below
    # SEMANTIC_SCHOLAR_API_KEY = "YOUR_API_KEY_HERE"
    SEMANTIC_SCHOLAR_API_KEY = None

    # --- Example Query String ---
    # Example derived from one of the triplets in 'file.json'
    example_triplet_string = "homocysteine, an amino acid linked to endothelial dysfunction"
    # Alternatively, a simpler query:
    # example_query = "inflammatory response APOE Alzheimer disease"

    # --- Instantiate and Run ---
    paper_finder = SemanticScholarPaperFinder(api_key=SEMANTIC_SCHOLAR_API_KEY)

    logging.info(f"\n" + "="*30 + f" FINDING PAPERS FOR QUERY STRING " + "="*30)

    # Use the finder instance directly (__call__ invokes forward)
    found_papers = paper_finder(query_string=example_triplet_string)

    if found_papers is not None:
        logging.info(f"Successfully found {len(found_papers)} papers for the query.")

        # --- Now YOU can save or process the found_papers list ---
        output_filename = "papers_for_query_string.json"
        logging.info(f"Attempting to save results to {output_filename}")
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(found_papers, f, indent=2, ensure_ascii=False)
            logging.info(f"Successfully saved results to {output_filename}")
        except Exception as e:
            logging.error(f"Failed to save results to {output_filename}: {e}")

        # Optionally print some info from the returned data
        if found_papers:
             print("\n--- First 3 Found Papers (Example Data): ---")
             for i, paper in enumerate(found_papers[:3]):
                 title = paper.get('title', 'N/A')
                 year = paper.get('year', 'N/A')
                 venue = paper.get('venue', 'N/A')
                 citations = paper.get('citationCount', 0)
                 authors = paper.get('authors', [])
                 author_names = [a.get('name', '?') for a in authors]

                 print(f"\nPaper {i+1}:")
                 print(f"  Title: {title}")
                 print(f"  Year: {year}")
                 print(f"  Venue: {venue}")
                 print(f"  Citations: {citations}")
                 print(f"  Authors: {', '.join(author_names)}")
                 # print(f"  Abstract: {paper.get('abstract', 'N/A')[:100]}...") # Example abstract snippet

    else:
        logging.error("Finding papers failed after retries. Check logs.")

    logging.info(f"\n" + "="*30 + f" SCRIPT COMPLETE " + "="*30)