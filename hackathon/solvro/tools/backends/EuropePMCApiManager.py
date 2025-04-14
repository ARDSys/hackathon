import requests
from typing import Optional, Dict, Any

class EuropePMCAPIManager:
    """
    A manager for interacting with the Europe PMC API.

    Attributes:
        BASE_URL (str): The base URL for the Europe PMC API.
        format (str): The response format, default is "json".
    """

    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"

    def __init__(self, format: str = "json"):
        """
        Initializes the EuropePMCAPIManager with a specified response format.

        Args:
            format (str): The response format, either "json" or "xml". Default is "json".
        """
        self.format = format

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, method: str = "GET"):
        """
        Sends a request to the Europe PMC API.

        Args:
            endpoint (str): The API endpoint to call.
            params (Optional[Dict[str, Any]]): Query parameters for the request. Default is None.
            method (str): The HTTP method to use (e.g., "GET", "POST"). Default is "GET".

        Returns:
            dict or str: The API response in JSON or text format, depending on the specified format.

        Raises:
            requests.exceptions.HTTPError: If the API request fails.
        """
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params["format"] = self.format

        response = requests.request(method, url, params=params)
        response.raise_for_status()
        return response.json() if self.format == "json" else response.text

    def search(self, query: str, result_type: str = "lite", **kwargs):
        """
        Searches the Europe PMC database.

        Args:
            query (str): The search query.
            result_type (str): The type of results to return ("lite", "core", etc.). Default is "lite".
            **kwargs: Additional query parameters.

        Returns:
            dict or str: The search results in JSON or text format.
        """
        params = {"query": query, "resultType": result_type, **kwargs}
        return self._request("search", params)

    def get_article(self, source: str, id_: str, **kwargs):
        """
        Retrieves a specific article by source and ID.

        Args:
            source (str): The source of the article (e.g., "MED").
            id_ (str): The ID of the article.
            **kwargs: Additional query parameters.

        Returns:
            dict or str: The article data in JSON or text format.
        """
        return self._request(f"article/{source}/{id_}", kwargs)

    def get_references(self, source: str, id_: str):
        """
        Retrieves references for a specific article.

        Args:
            source (str): The source of the article (e.g., "MED").
            id_ (str): The ID of the article.

        Returns:
            dict or str: The references data in JSON or text format.
        """
        return self._request(f"{source}/{id_}/references")

    def get_citations(self, source: str, id_: str):
        """
        Retrieves citations for a specific article.

        Args:
            source (str): The source of the article (e.g., "MED").
            id_ (str): The ID of the article.

        Returns:
            dict or str: The citations data in JSON or text format.
        """
        return self._request(f"{source}/{id_}/citations")

    def get_database_links(self, source: str, id_: str):
        """
        Retrieves database links for a specific article.

        Args:
            source (str): The source of the article (e.g., "MED").
            id_ (str): The ID of the article.

        Returns:
            dict or str: The database links data in JSON or text format.
        """
        return self._request(f"{source}/{id_}/databaseLinks")

    def get_labs_links(self, source: str, id_: str):
        """
        Retrieves lab links for a specific article.

        Args:
            source (str): The source of the article (e.g., "MED").
            id_ (str): The ID of the article.

        Returns:
            dict or str: The lab links data in JSON or text format.
        """
        return self._request(f"{source}/{id_}/labsLinks")

    def get_data_links(self, source: str, id_: str):
        """
        Retrieves data links for a specific article.

        Args:
            source (str): The source of the article (e.g., "MED").
            id_ (str): The ID of the article.

        Returns:
            dict or str: The data links in JSON or text format.
        """
        return self._request(f"{source}/{id_}/datalinks")

    def get_full_text_xml(self, id_: str):
        """
        Retrieves the full text of an article in XML format.

        Args:
            id_ (str): The ID of the article.

        Returns:
            str: The full text in XML format.
        """
        return self._request(f"{id_}/fullTextXML")

    def get_book_xml(self, id_: str):
        """
        Retrieves the book content of an article in XML format.

        Args:
            id_ (str): The ID of the article.

        Returns:
            str: The book content in XML format.
        """
        return self._request(f"{id_}/bookXML")

    def get_supplementary_files(self, id_: str):
        """
        Retrieves supplementary files for a specific article.

        Args:
            id_ (str): The ID of the article.

        Returns:
            dict or str: The supplementary files data in JSON or text format.
        """
        return self._request(f"{id_}/supplementaryFiles")

    def get_evaluations(self, source: str, id_: str):
        """
        Retrieves evaluations for a specific article.

        Args:
            source (str): The source of the article (e.g., "MED").
            id_ (str): The ID of the article.

        Returns:
            dict or str: The evaluations data in JSON or text format.
        """
        return self._request(f"evaluations/{source}/{id_}")

    def get_fields(self):
        """
        Retrieves the available fields for querying the Europe PMC API.

        Returns:
            dict or str: The fields data in JSON or text format.
        """
        return self._request("fields")

    def get_profile(self):
        """
        Retrieves the profile information of the Europe PMC API.

        Returns:
            dict or str: The profile data in JSON or text format.
        """
        return self._request("profile")

    def status_update_search(self, query: str, **kwargs):
        """
        Searches for status updates in the Europe PMC database.

        Args:
            query (str): The search query.
            **kwargs: Additional query parameters.

        Returns:
            dict or str: The search results in JSON or text format.
        """
        params = {"query": query, **kwargs}
        return self._request("status-update-search", params, method="POST")

    def custom_search(
            self,
            query: str,
            result_type: str = "lite",
            sort_by_citations: bool = False,
            sort_by_date: bool = False,
            **kwargs
    ):
        """
            Search for publications in the Europe PMC database using a keyword-based query.

            This method queries the Europe PMC RESTful API with optional sorting and result type control.

            Parameters:
            ----------
            query : str
                The search query string (e.g., "CRISPR", "cancer AND p53", "COVID-19").
            result_type : str, optional
                Level of detail in the results. Options:
                - "idlist": returns only IDs and sources.
                - "lite": returns basic metadata (default).
                - "core": returns full metadata including abstract, MeSH terms, citation counts, etc.
            sort_by_citations : bool, optional
                If True, sorts results by number of citations in descending order.
            sort_by_date : bool, optional
                If True, sorts results by publication date in descending order (most recent first).
            **kwargs : dict
                Additional query parameters supported by the Europe PMC API (e.g., pageSize, cursorMark).

            Returns:
            -------
            dict or str
                The API response in JSON (default) or XML format, depending on the `format` specified when
                initializing the EuropePMCAPIManager instance.


            """
        if sort_by_citations:
            query += " sort_cited:y"
        elif sort_by_date:
            query += " sort_date:y"
        params = {"query": query, "resultType": result_type, **kwargs}
        return self._request("search", params)

    def get_most_cited_in_period(
            self,
            keyword: str,
            start_year: int,
            end_year: int,
            result_type: str = "core",
            max_results: int = 25,
            **kwargs
    ):
        """
        Retrieve the most cited publications for a keyword within a specific publication year range.

        Parameters:
        ----------
        keyword : str
            Search keyword(s), e.g. "CRISPR", "cancer AND p53".
        start_year : int
            Start of the publication year range (inclusive).
        end_year : int
            End of the publication year range (inclusive).
        result_type : str, optional
            Result type: "core" (default), "lite", or "idlist".
        max_results : int, optional
            Maximum number of results to return (default: 25).
        **kwargs : dict
            Additional query parameters (e.g., pageSize, format).

        Returns:
        -------
        list
            A list of articles sorted by citation count (desc).
        """
        query = f"{keyword} AND PUB_YEAR:[{start_year} TO {end_year}] sort_cited:y"
        params = {
            "query": query,
            "resultType": result_type,
            "pageSize": max_results,
            **kwargs
        }
        result = self._request("search", params)
        return result.get("resultList", {}).get("result", [])


# Example usage:
if __name__ == "__main__":
    api = EuropePMCAPIManager()

    # Get articles related to "CRISPR", sorted by citation count
    top_cited = api.get_most_cited_in_period("CRISPR", 2023, 2024)

    for i, paper in enumerate(top_cited, 1):
        print(f"{i}. ({paper.get('pubYear')}) {paper.get('title')}")
        print(f"   Citations: {paper.get('citedByCount')}\n")