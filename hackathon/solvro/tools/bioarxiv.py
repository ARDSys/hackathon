from typing import Optional, Dict, Annotated, Any

import requests
from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.tools import tool, BaseTool
from langchain_core.runnables import RunnableConfig
from langchain_core.callbacks import CallbackManagerForToolRun
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.prebuilt import InjectedState
from langchain_core.tools import InjectedToolCallId
from dataclasses import dataclass


BASE_URL = "https://api.biorxiv.org"

class BioRxivAPIManager(BaseModel):
    """
    A manager class for interacting with the BioRxiv API.

    Attributes:
        server (str): The server to use for API requests (default is "biorxiv").
    """
    
    server: str = "biorxiv"

    def validate_server(cls, values):
        """Validate the server attribute."""
        # Add any server validation logic if necessary
        return values

    def fetch_details_by_date_range(
        self, start_date: str, end_date: str, cursor: int = 0,
        category: Optional[str] = None, format: str = "json"
    ):
        """
        Fetches article details within a specified date range.
        """
        url = f"{BASE_URL}/details/{self.server}/{start_date}/{end_date}/{cursor}/{format}"
        if category:
            url += f"?category={category.replace(' ', '_')}"
        return self._get(url)

    def fetch_details_by_doi(self, doi: str, format: str = "json"):
        """
        Fetches article details by DOI.
        """
        url = f"{BASE_URL}/details/{self.server}/{doi}/na/{format}"
        return self._get(url)


    def _get(self, url: str):
        """
        Sends a GET request to the specified URL.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json() if "json" in url else response.text
        except requests.RequestException as e:
            print(f"Error fetching data from {url}: {e}")
            return None


# Initialize the BioRxiv API manager
biorxiv_api = BioRxivAPIManager()

@tool("bioarxiv", parse_docstring=True)
def biorxiv_tool(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    BioRxivTool provides access to the bioRxiv preprint repository, enabling search and retrieval of the latest 
    non-peer-reviewed biomedical research articles. This tool supports querying by keywords, authors, or topics, 
    and returns metadata such as title, abstract, authors, and publication date. Useful for staying updated on 
    emerging scientific findings in biology, medicine, and related disciplines.
    
    Args:
        query: A category or topic to search for in bioRxiv.
        tool_call_id: Injected tool call ID.
        config: Runnable configuration.
        state: Injected state.

    Returns:
        A dictionary containing preprint information from the bioRxiv API.
    """
    return biorxiv_api.fetch_details_by_date_range(
        start_date="2025-03-21",
        end_date="2025-03-28",
        category=query
    )
