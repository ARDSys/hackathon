import csv
import io
import re
from urllib.parse import quote

import requests
from langchain.tools import tool


@tool
def search_pubmed_by_year(query: str) -> str:
    """Search PubMed by Year for publication trends over time.

    Args:
        query: The search query to find relevant publication trends on PubMed by Year

    Returns:
        A string containing the search results from PubMed by Year with trend information
    """
    # Base URL for PubMed by Year
    base_url = "https://esperr.github.io/pubmed-by-year/"

    try:
        # Create the query URL
        search_url = f"{base_url}?q1={quote(query)}"

        # Add a user-agent header to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Get the HTML page
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        html_content = response.text

        # First check if we got any results - more specific text matching to avoid false positives
        if (
            "Nothing was found for this search." in html_content
            or "Your search only retrieved <strong>" in html_content
        ):
            return f"No sufficient data found for query: '{query}'. PubMed by Year requires at least 500 results for a search to be graphed. Please try a different search term."

        # Try to get the CSV data directly
        # First, get the web search response
        data_url = None

        # Extract the CSV data URL from the JavaScript
        csv_url_pattern = r"var CSVdata = 'data:text/csv;charset=utf-8,(.*?)';"
        csv_url_match = re.search(csv_url_pattern, html_content)

        if csv_url_match:
            # If we found a direct URL to the CSV data
            csv_data_encoded = csv_url_match.group(1)
            csv_data_string = requests.utils.unquote(csv_data_encoded)

            # Parse the CSV data
            csv_reader = csv.reader(io.StringIO(csv_data_string))
            rows = list(csv_reader)

            if len(rows) >= 2:  # We have headers and at least one row of data
                headers = rows[0]
                data_points = []

                # Extract the relevant data
                for row in rows[1:]:
                    if len(row) >= 2:  # We need at least year and one data point
                        year = row[0]
                        proportion = float(row[1])

                        # Get count from the original HTML content
                        # This is approximate, as the CSV only contains proportions
                        count_pattern = rf"{year}\".*?(\d[\d,]*)\s+citations"
                        count_match = re.search(count_pattern, html_content)
                        count = (
                            count_match.group(1).replace(",", "")
                            if count_match
                            else "N/A"
                        )

                        data_points.append(
                            {"year": year, "proportion": proportion, "count": count}
                        )

                # Format the results
                result = f"Publication trends for query: '{query}'\n\n"
                result += "Year\t|\tCount\t|\tProportion (per 100,000)\n"
                result += "-" * 50 + "\n"

                # Sort by year
                data_points.sort(key=lambda x: x["year"])

                for item in data_points:
                    result += (
                        f"{item['year']}\t|\t{item['count']}\t|\t{item['proportion']}\n"
                    )

                result += f"\nThese results show how publications matching '{query}' have changed over time relative to the entire PubMed database."
                result += f"\n\nView the full interactive visualization: {search_url}"

                return result

        # If we couldn't extract the CSV data, fall back to the original pattern extraction
        data_points = []
        # Pattern matches: data.addRow(['2020', {v: 123.45, f: "456 citations..."}]);
        row_pattern = r"data\.addRow\(\[\s*['\"](\d+)['\"],\s*\{v:\s*([\d\.]+),\s*f:\s*['\"](\d[\d,]*)\s+citations[^'\"]*['\"]\}\s*\]\);"

        matches = re.findall(row_pattern, html_content)
        if matches:
            # We found structured data from the chart
            data_points = [
                {
                    "year": year,
                    "proportion": float(proportion),
                    "count": count.replace(",", ""),
                }
                for year, proportion, count in matches
            ]

            # If we have data points, return them even if the original page showed an error
            if data_points:
                # Format the results
                result = f"Publication trends for query: '{query}'\n\n"
                result += "Year\t|\tCount\t|\tProportion (per 100,000)\n"
                result += "-" * 50 + "\n"

                # Sort by year
                data_points.sort(key=lambda x: x["year"])

                for item in data_points:
                    result += (
                        f"{item['year']}\t|\t{item['count']}\t|\t{item['proportion']}\n"
                    )

                result += f"\nThese results show how publications matching '{query}' have changed over time relative to the entire PubMed database."
                result += f"\n\nView the full interactive visualization: {search_url}"

                return result

        # Fallback for when specific patterns aren't found
        return f"""
        Search results for '{query}' on PubMed by Year
        
        To view the complete visualization with year-by-year publication trends,
        please visit: {search_url}
        
        This tool helps identify publication trends by comparing your search results 
        for each year to the database as a whole, showing how interest in your topic 
        has changed over time in the scientific literature.
        """

    except requests.RequestException as e:
        return f"Error accessing PubMed by Year: {str(e)}"
    except Exception as e:
        return f"Unexpected error processing PubMed by Year results: {str(e)}"
