import os
from pathlib import Path

import pandas as pd
import requests

from agents import function_tool


@function_tool
def query_prime_kg(keyword: str):
    """
    Query the PrimeKG database for a given keyword. Returns a string representation of protein-protein interactions.

    PrimeKG is a biomedical knowledge graph that contains various biological relationships,
    including protein-protein interactions (PPI). This function specifically focuses on finding
    protein/gene relationships given a keyword search.

    Args:
        keyword (str): The keyword to search for in gene/protein names or IDs.

    Returns:
        str: A string containing the matched protein/gene information and all its immediate
             protein-protein interactions. Returns an error message if no matches are found
             or if the query fails.
    """
    try:
        # Load the PrimeKG dataset
        current_dir = Path(__file__).parent
        prime_kg_path = os.path.join(current_dir, "prime_kg", "prime_kg_dataset.csv")

        if not os.path.exists(prime_kg_path):
            print("PrimeKG dataset not found. Downloading it now...")
            load_prime_kg()
            if not os.path.exists(prime_kg_path):
                return "Failed to download PrimeKG dataset. Please try again later."

        df = pd.read_csv(prime_kg_path)

        # Find matches in either x_name/x_id or y_name/y_id
        matching_x = df[
            (df["x_name"].str.contains(keyword, case=False, na=False))
            | (df["x_id"].astype(str).str.contains(keyword, case=False, na=False))
        ]

        matching_y = df[
            (df["y_name"].str.contains(keyword, case=False, na=False))
            | (df["y_id"].astype(str).str.contains(keyword, case=False, na=False))
        ]

        if matching_x.empty and matching_y.empty:
            return f"No proteins/genes found matching keyword: {keyword}"

        result = []

        # Process matches where keyword is in x_name/x_id
        for _, row in matching_x.iterrows():
            result.append(
                f"Protein/Gene: {row['x_name']} (ID: {row['x_id']} from {row['x_source']})"
            )
            result.append(
                f"  -> {row['relation']} -> {row['y_name']} "
                f"(ID: {row['y_id']} from {row['y_source']})"
            )

        # Process matches where keyword is in y_name/y_id
        for _, row in matching_y.iterrows():
            result.append(
                f"Protein/Gene: {row['x_name']} (ID: {row['x_id']} from {row['x_source']})"
            )
            result.append(
                f"  -> {row['relation']} -> {row['y_name']} "
                f"(ID: {row['y_id']} from {row['y_source']})"
            )

        return "\n".join(result)

    except Exception as e:
        return f"Error querying PrimeKG: {str(e)}"


def load_prime_kg():
    """
    Download the PrimeKG dataset and save it to the specified directory.

    Args:
        output_dir (str): Directory where the file will be saved. Defaults to "data".
    """
    # Create output directory if it doesn't exist
    current_dir = Path(__file__).parent

    # Paths to local files
    directory_path = os.path.join(
        current_dir,
        "prime_kg",
    )
    os.makedirs(directory_path, exist_ok=True)

    # Check if file already exists
    filename = "prime_kg_dataset.csv"
    output_path = os.path.join(directory_path, filename)
    if os.path.exists(output_path):
        print(f"PrimeKG dataset already exists at: {output_path}")
        return output_path

    # URL for the PrimeKG dataset
    url = "https://dataverse.harvard.edu/api/access/datafile/6180620"

    try:
        # Send GET request
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Save the file
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"File downloaded successfully to: {output_path}")
        return output_path

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
        return None


if __name__ == "__main__":
    print(query_prime_kg("PSMC4"))
