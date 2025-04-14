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
    # Import here to avoid circular imports
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
