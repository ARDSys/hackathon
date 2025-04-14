"""Functions for Hypegen agents.

This module contains function definitions that are registered with agents for execution.
"""

import os
from typing import Annotated

import requests


def response_to_query_perplexity(
    query: Annotated[
        str,
        """the query for the paper search. The query must consist of relevant keywords separated by +""",
    ],
) -> str:
    """Search for academic papers using the Perplexity API.

    Args:
        query: The search query with keywords separated by +

    Returns:
        The response data from Perplexity API
    """
    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "Search scientific papers for the most relevant papers on the query. Return the top 10 results.",
            },
            {"role": "user", "content": query},
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        "search_domain_filter": None,
        "return_images": False,
        "return_related_questions": False,
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
        "response_format": None,
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('PPLX_API_KEY')}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    # Check response status
    if response.status_code == 200:
        response_data = response.json()
    else:
        response_data = (
            f"Request failed with status code {response.status_code}: {response.text}"
        )

    return response_data


def response_to_query(
    query: Annotated[
        str,
        """the query for the paper search. The query must consist of relevant keywords separated by +""",
    ],
) -> str:
    """Search for academic papers using the Semantic Scholar API.

    Args:
        query: The search query with keywords separated by +

    Returns:
        The response data from Semantic Scholar API
    """
    # Define the API endpoint URL
    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    # More specific query parameter
    query_params = {"query": {query}, "fields": "title,abstract,openAccessPdf,url"}

    # Define headers with API key
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers = {"x-api-key": api_key}
    else:
        headers = {}

    # Send the API request
    response = requests.get(url, params=query_params, headers=headers)

    # Check response status
    if response.status_code == 200:
        response_data = response.json()
        # Process and print the response data as needed
    else:
        response_data = (
            f"Request failed with status code {response.status_code}: {response.text}"
        )

    return response_data


def rate_novelty_feasibility(
    hypothesis: Annotated[str, "the research hypothesis."],
) -> str:
    """Rate the novelty and feasibility of a research idea against the literature.

    Args:
        hypothesis: The research hypothesis to evaluate

    Returns:
        A rating of novelty and feasibility from 1 to 10
    """
    from .agents import novelty_admin, novelty_assistant

    res = novelty_admin.initiate_chat(
        novelty_assistant,
        clear_history=True,
        silent=False,
        max_turns=10,
        message=f"""Rate the following research hypothesis\n\n{hypothesis}. \n\nCall the function three times at most, but not in parallel. Wait for the results before calling the next function. """,
        summary_method="reflection_with_llm",
        summary_args={
            "summary_prompt": "Return all the results of the analysis as is."
        },
    )

    return res.summary

import urllib.request
import urllib.parse
import json
import os

def annotate_text_with_bioportal(text):
    """
    Annotate a biomedical text using BioPortal Annotator API.
    Returns a list of ontology term URIs.
    """
    api_key = os.getenv("BIOPORTAL_API_KEY")
    url = "http://data.bioontology.org/annotator"
    params = {
        "text": text,
        "ontologies": "GO,DOID,UBERON,CL,MESH",
        "longest_only": "true",
        "exclude_numbers": "true",
        "apikey": api_key
    }

    encoded_params = urllib.parse.urlencode(params)
    full_url = f"{url}?{encoded_params}"

    try:
        with urllib.request.urlopen(full_url) as response:
            result = json.loads(response.read())
    except Exception as e:
        print("Error:", e)
        return []

    uris = []
    for item in result:
        annotated_class = item.get("annotatedClass", {})
        uri = annotated_class.get("@id")
        if uri:
            uris.append(uri)

    return uris

def build_tree_with_description(start_id, index, visited=None):
    """

    """
    if visited is None:
        visited = set()
    if start_id in visited:
        return {"id": start_id, "label": index[start_id].get("lbl", ""), "description": "<cyclic>"}

    visited.add(start_id)
    node = index.get(start_id)
    if not node:
        return {"id": start_id, "label": "<not found>", "description": "<not found>"}

    label = node.get("lbl", "")
    description = node.get("meta", {}).get("definition", {}).get("val", "")

    parents = node.get("meta", {}).get("basicPropertyValues", [])
    parent_ids = [
        p["val"].split("/")[-1].replace(":", "_")
        for p in parents
        if "is_a" in p["pred"] or p["pred"].endswith("#subClassOf")
    ]

    return {
        "id": start_id,
        "label": label,
        "description": description,
        "parents": [build_tree_with_description(pid, index, visited.copy()) for pid in parent_ids]
    }


import json
import re

def build_ontology_trees_from_bioportal_output(bioportal_output_text):
    """
    This function parses the annotated output (text format) from BioPortal,
    extracts term URIs and their corresponding ontologies (GO or HP),
    and then loads local JSON files containing the full ontology structure
    to build recursive trees for each matched term.
    """
    uri_ontology_map = []
    lines = bioportal_output_text.splitlines()
    current = {}
    for line in lines:
        if line.startswith("Ontology:"):
            current["ontology"] = line.replace("Ontology:", "").strip().lower()
        elif line.startswith("URI:"):
            current["uri"] = line.replace("URI:", "").strip()
            uri_ontology_map.append(current)
            current = {}

    with open("data/go.json", "r") as f:
        go_data = json.load(f)
    with open("data/hp.json", "r") as f:
        hp_data = json.load(f)

    go_index = {entry["id"].split("/")[-1].replace(":", "_"): entry for entry in go_data.get("graphs", [])[0].get("nodes", [])}
    hp_index = {entry["id"].split("/")[-1].replace(":", "_"): entry for entry in hp_data.get("graphs", [])[0].get("nodes", [])}

    results = {"gene_ontology": {}, "human_phenotype": {}}

    for item in uri_ontology_map:
        uri = item["uri"]
        ontology = item["ontology"]
        obo_id_match = re.search(r'([A-Z]+[_:]\d+)', uri)
        if not obo_id_match:
            continue
        obo_id = obo_id_match.group(1).replace(":", "_")

        if "go" in ontology:
            tree = build_tree_with_description(obo_id, go_index)
            results["gene_ontology"][obo_id] = tree
        elif "hp" in ontology:
            tree = build_tree_with_description(obo_id, hp_index)
            results["human_phenotype"][obo_id] = tree

    return results


def annotate_and_expand_ontologies(text: str) -> dict:
    """
    Annotate a comma-separated list of biomedical terms using BioPortal,
    then expand those terms using local GO and HP ontologies.

    Args:
        text (str): Comma-separated biomedical terms (e.g. "inflammation, amyloid beta")

    Returns:
        dict: {
            "gene_ontology": { GO_ID: tree_structure },
            "human_phenotype": { HP_ID: tree_structure }
        }
    """
    all_uris = []
    terms = [t.strip() for t in text.split(",") if t.strip()]
    output_lines = [f"Results for terms: {text}\n"]

    for term in terms:
        uris = annotate_text_with_bioportal(term)
        for uri in uris:
            label = uri.split("/")[-1]
            if "GO_" in uri:
                output_lines.append(f"{label}\nOntology: http://data.bioontology.org/ontologies/go\nURI: {uri}\n")
            elif "HP_" in uri:
                output_lines.append(f"{label}\nOntology: http://data.bioontology.org/ontologies/hp\nURI: {uri}\n")
        all_uris.extend(uris)

    if not all_uris:
        return {"message": "No ontology terms found for any of the provided terms."}

    output_text = "\n".join(output_lines)

    return build_ontology_trees_from_bioportal_output(output_text)


