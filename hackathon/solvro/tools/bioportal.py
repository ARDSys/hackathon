import os

from urllib.parse import quote
import requests
import logging
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any, Annotated
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool, tool, InjectedToolCallId
from pydantic import Field
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import InjectedState


logger = logging.getLogger(__name__)

class BioPortalClient(BaseModel):
    """
    Wrapper around the BioPortal API.

    This wrapper will use the BioPortal API to conduct searches and
    fetch term details from ontologies.

    Parameters:
        api_key: Your API key for accessing the BioPortal API.
    """

    api_key: str = Field(default_factory=lambda: os.environ.get('BIOPORTAL_API_KEY', ''))
    headers: Dict[str, str] = {}

    @field_validator('api_key')
    def validate_api_key(cls, api_key: str) -> str:
        """Validate that the API key is provided."""
        if not api_key:
            raise ValueError("API key must be provided as parameter or in BIOPORTAL_API_KEY environment variable.")
        return api_key
    
    def model_post_init(self, __context) -> None:
        """Set up headers after initialization."""
        self.headers = {
            "Authorization": f"apikey token={self.api_key}"
        }

    BASE_URL: str = "https://data.bioontology.org"

    def search_terms(self, query: str, ontologies: Optional[List[str]] = None,
                     exact_match: bool = False, require_definitions: bool = False,
                     suggest: bool = False) -> Dict[str, Any]:
        """
        Search for terms in BioPortal.

        :param query: Search query string.
        :param ontologies: List of ontology acronyms to restrict the search.
        :param exact_match: If True, only exact matches are returned.
        :param require_definitions: If True, only terms with definitions are returned.
        :param suggest: If True, enables type-ahead suggestions.
        :return: JSON response from the API.
        """
        params = {
            "q": query,
            "require_exact_match": str(exact_match).lower(),
            "require_definitions": str(require_definitions).lower(),
            "suggest": str(suggest).lower(),
            "apikey": self.api_key
        }
        if ontologies:
            params["ontologies"] = ",".join(ontologies)
        try:
            response = requests.get(f"{self.BASE_URL}/search", headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error during search_terms: {e}")
            raise

    def list_ontologies(self) -> Dict[str, Any]:
        """
        Retrieve a list of available ontologies.

        :return: JSON response from the API.
        """
        try:
            response = requests.get(f"{self.BASE_URL}/ontologies", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error during list_ontologies: {e}")
            raise

    def get_class(self, ontology_acronym: str, class_id: str) -> Dict[str, Any]:
        """
        Get details of a specific class within an ontology.

        :param ontology_acronym: Acronym of the ontology.
        :param class_id: Full URI or ID of the class.
        :return: JSON response from the API.
        """
        encoded_class_id = quote(class_id, safe='')
        url = f"{self.BASE_URL}/ontologies/{ontology_acronym}/classes/{encoded_class_id}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error during get_class: {e}")
            raise


# Initialize the BioPortal client
bioportal_client = BioPortalClient()

@tool("bioportal", parse_docstring=True)
def bioportal_tool(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    BioPortalTool provides access to the BioPortal API, a comprehensive repository of biomedical ontologies.
    This tool enables ontology search, term annotation, ontology recommendations, and term mappings,
    facilitating semantic enrichment and integration of biomedical data. Ideal for applications in clinical,
    genomic, and public health domains.
    
    Args:
        query: A biomedical term or concept to search for in BioPortal.

    Returns:
        A dictionary containing the search results from BioPortal.
    """
    return bioportal_client.search_terms(query)