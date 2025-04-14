import requests
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from hackathon.modules.Module import Module

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Choose ARA Endpoint
ARA_TRAPI_ENDPOINT = "https://bte.transltr.io/v1/query"
# ARA_TRAPI_ENDPOINT = "https://aragorn.renci.org/1.4/query"

# Timeout for the API request in seconds
TIMEOUT = 600 # 10 minutes



class AraPathFinder(Module):
    """
    Finds A->B->C (3-node/2-edge) paths using an ARA, processes all results,
    returns the simplified structured path list, and saves it to JSON.
    """
    def __init__(self,
                 ara_url: str = ARA_TRAPI_ENDPOINT,
                 timeout: int = TIMEOUT,
                 output_filename_template: str = "{start_name}_{end_name}_paths.json"):
        """
        Initializes the finder.

        Args:
            ara_url: The TRAPI endpoint URL of the ARA.
            timeout: Request timeout in seconds.
            output_filename_template: A template for the output JSON filename.
                                      Placeholders {start_name} and {end_name} will be replaced.
        """
        super().__init__()
        self.ara_url = ara_url
        self.timeout = timeout
        self.output_filename_template = output_filename_template
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
        logging.info(f"AraPathFinder initialized. Target ARA: {self.ara_url}, Timeout: {self.timeout}s")

    def _send_ara_query(self, request_body: Dict[str, Any], query_description: str) -> Optional[Dict[str, Any]]:
        """Helper: Sends query, handles response/errors, returns TRAPI 'message'."""
        logging.info(f"Sending {query_description} query to ARA: {self.ara_url}")
        logging.debug(f"Request Body: {json.dumps(request_body, indent=2)}")
        try:
            response = self.session.post(self.ara_url,
                                         json=request_body,
                                         timeout=self.timeout)
            response.raise_for_status()
            response_json = response.json()

            message = None
            if "message" in response_json:
                message = response_json["message"]
            elif "workflow" in response_json and isinstance(response_json["workflow"], list) and response_json["workflow"]:
                 potential_message = response_json["workflow"][0].get("message")
                 if potential_message:
                     logging.warning("Response missing top-level 'message', extracted from 'workflow'.")
                     message = potential_message

            if not message:
                 logging.error(f"ARA response for {query_description} missing 'message' key.")
                 logging.debug(f"Raw response: {response.text}")
                 return None

            results_count = len(message.get("results", []))
            kg_node_count = len(message.get("knowledge_graph", {}).get("nodes", {}))
            status = response_json.get("status", "Unknown")
            logging.info(f"ARA {query_description} query successful. Status: '{status}', Results Returned: {results_count}, KG Nodes: {kg_node_count}.")

            return message

        # --- Standard Error Handling ---
        except requests.exceptions.Timeout:
            logging.error(f"ARA {query_description} query timed out to {self.ara_url}.")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"ARA {query_description} query request failed: {e}")
            try: logging.error(f"Response status: {e.response.status_code}, Body: {e.response.text}")
            except AttributeError: pass
            return None
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON response from ARA: {e}")
            try: logging.error(f"Raw text: {response.text}")
            except Exception: pass
            return None
        except Exception as e:
             logging.exception(f"Unexpected error during ARA query: {e}")
             return None

    def _extract_structured_path_data(self, message: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
        """
        Parses the TRAPI message and extracts structured path data for 3-node paths.

        Args:
            message: The TRAPI message dictionary.

        Returns:
            A list where each element is a list of dictionaries representing nodes
            in a path: [[nodeA_data, nodeB_data, nodeC_data], [path2_nodeA, ...], ...]
        """
        structured_path_list = []
        if not message:
            logging.warning("Cannot extract paths, message is empty.")
            return structured_path_list

        results = message.get("results", [])
        kg_nodes = message.get("knowledge_graph", {}).get("nodes", {})

        if not results:
            logging.info("No results found in the message to extract paths from.")
            return structured_path_list
        if not kg_nodes:
            logging.warning("Knowledge graph nodes are missing, cannot lookup full node data.")
            return structured_path_list

        num_nodes_in_path = 3 # Hardcoded for A->B->C

        logging.info(f"Extracting structured path data from {len(results)} results for {num_nodes_in_path}-node paths...")

        processed_count = 0
        for result in results:
            # No MAX_PATHS limit applied here, processing all results
            node_bindings = result.get("node_bindings", {})
            current_path_nodes = []
            path_complete = True

            for i in range(num_nodes_in_path): # Loop 0, 1, 2
                node_key = f"n{i}"
                if node_key not in node_bindings:
                     logging.warning(f"Skipping result: Expected node key '{node_key}' not found. Bindings: {node_bindings}")
                     path_complete = False
                     break
                node_id = node_bindings.get(node_key, [{}])[0].get('id')
                if not node_id:
                    logging.warning(f"Skipping result: missing binding ID for '{node_key}'. Bindings: {node_bindings}")
                    path_complete = False
                    break
                node_data_from_kg = kg_nodes.get(node_id, {})
                node_name = node_data_from_kg.get('name', node_id)
                node_categories = node_data_from_kg.get('categories', [])
                node_category = node_categories[0] if node_categories else "biolink:NamedThing"
                current_path_nodes.append({
                    "name": node_name if node_name else node_id,
                    "curie": node_id,
                    "category": node_category
                })

            if path_complete:
                structured_path_list.append(current_path_nodes)
                processed_count += 1 # Increment even though we process all

        logging.info(f"Extracted data for {processed_count} structured paths.") # Log the number processed
        return structured_path_list

    def _save_results_to_json(self, data: List[List[Dict[str, Any]]], filename: str):
        """Saves the extracted structured path data to a JSON file."""
        if not data:
            logging.warning("No structured path data provided. Nothing to save to JSON.")
            return False # Indicate saving did not happen

        logging.info(f"Attempting to save {len(data)} structured paths to {filename}")
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            logging.info(f"Successfully saved structured path data to {filename}")
            return True # Indicate success
        except Exception as e:
            logging.error(f"Failed to save structured data to JSON file '{filename}': {e}")
            return False # Indicate failure


    def forward(self, start_curie: str, start_category: str, end_curie: str, end_category: str) -> Optional[List[List[Dict[str, Any]]]]:
        """
        Orchestrates finding A->B->C paths, extracting structured data,
        saving to JSON, and returning the structured data.

        Args:
            start_curie: CURIE of the starting node A.
            start_category: Biolink category of node A.
            end_curie: CURIE of the ending node C.
            end_category: Biolink category of node C.

        Returns:
            A list of structured paths found, or None if the query failed.
            Each path is a list of node dictionaries [{'name':.., 'curie':.., 'category':..}].
        """
        hop_count = 3 # Fixed for this class
        num_edges = hop_count - 1
        query_description = f"{hop_count}-Node ({num_edges}-Hop) Path Query"
        logging.info(f"Constructing {query_description} query: {start_curie} -> B -> {end_curie}")

        # Build Query Graph for A->B->C
        nodes = {
            "n0": {"ids": [start_curie], "categories": [start_category]}, # A
            "n1": {},                                                     # B (Intermediate, unspecified)
            "n2": {"ids": [end_curie], "categories": [end_category]}     # C
        }
        edges = {
            "e0": {"subject": "n0", "object": "n1"}, # A->B
            "e1": {"subject": "n1", "object": "n2"}  # B->C
        }
        query_graph = {"nodes": nodes, "edges": edges}
        request_body = {"message": {"query_graph": query_graph}}

        # Send Query
        message = self._send_ara_query(request_body, query_description)

        # Extract Data
        structured_data = []
        start_node_name_for_file = "unknown"
        end_node_name_for_file = "unknown"

        if message:
            # Attempt to get names for filename before full extraction
            try:
                start_node_name_for_file = message.get("knowledge_graph", {}).get("nodes", {}).get(start_curie, {}).get('name', start_curie).replace(" ", "_").replace("/", "_")
                end_node_name_for_file = message.get("knowledge_graph", {}).get("nodes", {}).get(end_curie, {}).get('name', end_curie).replace(" ", "_").replace("/", "_")
            except Exception:
                 logging.warning("Could not retrieve start/end names for filename generation.")

            structured_data = self._extract_structured_path_data(message)
        else:
            logging.error("ARA Query Failed or Timed Out. Cannot extract path data.")
            return None # Return None if query failed

        # Determine filename
        output_filename = self.output_filename_template.format(
            start_name=start_node_name_for_file,
            end_name=end_node_name_for_file
        )

        # Save Data
        self._save_results_to_json(structured_data, output_filename)

        # Return Data
        return structured_data


# --- Main Execution ---
if __name__ == "__main__":
    # Define inputs A (Inflammatory Response) and C (Alzheimer's Disease)
    start_curie_A = "GO:0006954"       # Inflammatory Response
    start_category_A = "biolink:BiologicalProcess"
    end_curie_C = "MONDO:0004975"      # Alzheimer's Disease
    end_category_C = "biolink:Disease"

    # Instantiate finder
    # You can customize the filename template here if needed
    path_finder = AraPathFinder(
        output_filename_template="{start_name}_to_{end_name}_paths.json"
    )

    # --- Run the forward method ---
    logging.info(f"\n" + "="*30 + f" EXECUTING 3-NODE PATH FINDING VIA FORWARD METHOD " + "="*30)

    extracted_paths = path_finder( # Use the __call__ syntax which invokes forward
        start_curie=start_curie_A,
        start_category=start_category_A,
        end_curie=end_curie_C,
        end_category=end_category_C
    )

    # --- Check results ---
    if extracted_paths is not None:
        logging.info(f"Processing complete. Found and processed {len(extracted_paths)} paths.")
        logging.info(f"Results saved to the JSON file specified in previous logs.")
        # Optionally print the first few results from the returned list
        if extracted_paths:
             print("\n--- First few extracted paths (example): ---")
             for i, path in enumerate(extracted_paths[:5]):
                 node_names = [node['name'] for node in path]
                 print(f"Path {i+1}: {' -> '.join(node_names)}")

    else:
        logging.error("Pathfinding process failed. Check logs for details.")

    logging.info(f"\n" + "="*30 + f" SCRIPT COMPLETE " + "="*30)