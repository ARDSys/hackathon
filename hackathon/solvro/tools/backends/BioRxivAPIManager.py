import requests
from typing import Optional, Union

# Base URL for the BioRxiv API
BASE_URL = "https://api.biorxiv.org"

class BioRxivAPIManager:
    """
    A manager class for interacting with the BioRxiv API.

    Attributes:
        server (str): The server to use for API requests (default is "biorxiv").
    """

    def __init__(self, server: str = "biorxiv"):
        """
        Initializes the BioRxivAPIManager with the specified server.

        Args:
            server (str): The server to use for API requests (default is "biorxiv").
        """
        self.server = server

    def _get(self, url: str):
        """
        Sends a GET request to the specified URL.

        Args:
            url (str): The URL to send the GET request to.

        Returns:
            dict or str: The API response in JSON or XML format, or None if an error occurs.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json() if "json" in url else response.text
        except requests.RequestException as e:
            print(f"Error fetching data from {url}: {e}")
            return None


    def fetch_details_by_date_range(
        self, start_date: str, end_date: str, cursor: int = 0,
        category: Optional[str] = None, format: str = "json"
    ):
        """
        Fetches article details within a specified date range.

        Args:
            start_date (str): The start date in YYYY-MM-DD format.
            end_date (str): The end date in YYYY-MM-DD format.
            cursor (int): The pagination cursor (default is 0).
            category (Optional[str]): The category of articles (default is None).
            format (str): The response format, either "json" or "xml" (default is "json").

        Returns:
            dict or str: The API response in JSON or XML format, or None if an error occurs.
        """
        url = f"{BASE_URL}/details/{self.server}/{start_date}/{end_date}/{cursor}/{format}"
        if category:
            url += f"?category={category.replace(' ', '_')}"
        return self._get(url)

    def fetch_details_by_doi(self, doi: str, format: str = "json"):
        """
        Fetches article details by DOI.

        Args:
            doi (str): The DOI of the article.
            format (str): The response format, either "json" or "xml" (default is "json").

        Returns:
            dict or str: The API response in JSON or XML format, or None if an error occurs.
        """
        url = f"{BASE_URL}/details/{self.server}/{doi}/na/{format}"
        return self._get(url)

    def fetch_published_details_by_date(
        self, start_date: str, end_date: str, cursor: int = 0, format: str = "json"
    ):
        """
        Fetches published article details within a specified date range.

        Args:
            start_date (str): The start date in YYYY-MM-DD format.
            end_date (str): The end date in YYYY-MM-DD format.
            cursor (int): The pagination cursor (default is 0).
            format (str): The response format, either "json" or "xml" (default is "json").

        Returns:
            dict or str: The API response in JSON or XML format, or None if an error occurs.
        """
        url = f"{BASE_URL}/pub/{start_date}/{end_date}/{cursor}/{format}"
        return self._get(url)

    def fetch_publication_metadata_by_doi(self, doi: str, format: str = "json"):
        """
        Fetches metadata for a published article by DOI.

        Args:
            doi (str): The DOI of the article.
            format (str): The response format, either "json" or "xml" (default is "json").

        Returns:
            dict or str: The API response in JSON or XML format, or None if an error occurs.
        """
        url = f"{BASE_URL}/pubs/{self.server}/{doi}/na/{format}"
        return self._get(url)

    def fetch_publisher_data(
        self, publisher_prefix: str, start_date: str, end_date: str, cursor: int = 0
    ):
        """
        Fetches data for a specific publisher within a date range.

        Args:
            publisher_prefix (str): The publisher prefix.
            start_date (str): The start date in YYYY-MM-DD format.
            end_date (str): The end date in YYYY-MM-DD format.
            cursor (int): The pagination cursor (default is 0).

        Returns:
            dict or str: The API response in JSON or XML format, or None if an error occurs.
        """
        url = f"{BASE_URL}/publisher/{publisher_prefix}/{start_date}/{end_date}/{cursor}"
        return self._get(url)

    def fetch_summary_statistics(self, interval: str = "m", format: str = "json"):
        """
        Fetches summary statistics for the API.

        Args:
            interval (str): The interval for statistics, e.g., "d" (daily), "m" (monthly) (default is "m").
            format (str): The response format, either "json" or "xml" (default is "json").

        Returns:
            dict or str: The API response in JSON or XML format, or None if an error occurs.
        """
        url = f"{BASE_URL}/sum/{interval}/{format}"
        return self._get(url)

    def fetch_usage_statistics(self, interval: str = "m", format: str = "json"):
        """
        Fetches usage statistics for the API.

        Args:
            interval (str): The interval for statistics, e.g., "d" (daily), "m" (monthly) (default is "m").
            format (str): The response format, either "json" or "xml" (default is "json").

        Returns:
            dict or str: The API response in JSON or XML format, or None if an error occurs.
        """
        url = f"{BASE_URL}/usage/{interval}/{format}"
        return self._get(url)



# Example usage
if __name__ == "__main__":
    manager = BioRxivAPIManager(server="biorxiv")

    # Fetch details for articles in a specific date range and category
    # result = manager.fetch_details_by_date_range("2025-03-21", "2025-03-28", category="cell_biology")
    # if result:
    #     print(f"Found {result['messages'][0]['count']} articles.")
    #     for paper in result["collection"][:3]:  # just preview 3
    #         print(f"- {paper['title']} ({paper['date']})")

    result = manager.fetch_usage_statistics(interval="m", format="json")
    if result:
        print(f"Usage statistics: {result}")
    else:
        print("Failed to fetch usage statistics.")