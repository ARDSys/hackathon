import os
from enum import Enum
from typing import List, Optional, Dict, Any, Union

from agents import function_tool
from firecrawl import FirecrawlApp


class ScientificSource(Enum):
    """Enum for common scientific resources to search with Firecrawl."""

    PUBMED = "pubmed"
    BIORXIV = "biorxiv"
    MEDRXIV = "medrxiv"
    NIH = "nih"
    NATURE = "nature"
    SCIENCE = "science"
    CELL = "cell"
    LANCET = "lancet"
    BMJ = "bmj"
    NEJM = "nejm"
    FRONTIERS = "frontiers"
    PLOS = "plos"
    WHO = "who"
    CDC = "cdc"
    CUSTOM = "custom"  # For any custom site not in the predefined list


# Mapping of sources to their domain and search optimization
SOURCE_CONFIG = {
    ScientificSource.PUBMED: {
        "domain": "pubmed.ncbi.nlm.nih.gov",
        "query_template": "{keyword}",  # Basic search
        "advanced_template": "{keyword} {modifiers}",  # With modifiers like year, author
    },
    ScientificSource.BIORXIV: {
        "domain": "biorxiv.org",
        "query_template": "{keyword}",
        "advanced_template": "{keyword} {modifiers}",
    },
    ScientificSource.MEDRXIV: {
        "domain": "medrxiv.org",
        "query_template": "{keyword}",
        "advanced_template": "{keyword} {modifiers}",
    },
    ScientificSource.NIH: {
        "domain": "nih.gov",
        "query_template": "{keyword} research",
        "advanced_template": "{keyword} {modifiers} research",
    },
    ScientificSource.NATURE: {
        "domain": "nature.com",
        "query_template": "{keyword}",
        "advanced_template": "{keyword} {modifiers}",
    },
    ScientificSource.SCIENCE: {
        "domain": "science.org",
        "query_template": "{keyword}",
        "advanced_template": "{keyword} {modifiers}",
    },
    ScientificSource.CELL: {
        "domain": "cell.com",
        "query_template": "{keyword}",
        "advanced_template": "{keyword} {modifiers}",
    },
    ScientificSource.LANCET: {
        "domain": "thelancet.com",
        "query_template": "{keyword}",
        "advanced_template": "{keyword} {modifiers}",
    },
    ScientificSource.BMJ: {
        "domain": "bmj.com",
        "query_template": "{keyword}",
        "advanced_template": "{keyword} {modifiers}",
    },
    ScientificSource.NEJM: {
        "domain": "nejm.org",
        "query_template": "{keyword}",
        "advanced_template": "{keyword} {modifiers}",
    },
    ScientificSource.FRONTIERS: {
        "domain": "frontiersin.org",
        "query_template": "{keyword}",
        "advanced_template": "{keyword} {modifiers}",
    },
    ScientificSource.PLOS: {
        "domain": "plos.org",
        "query_template": "{keyword}",
        "advanced_template": "{keyword} {modifiers}",
    },
    ScientificSource.WHO: {
        "domain": "who.int",
        "query_template": "{keyword}",
        "advanced_template": "{keyword} {modifiers}",
    },
    ScientificSource.CDC: {
        "domain": "cdc.gov",
        "query_template": "{keyword}",
        "advanced_template": "{keyword} {modifiers}",
    },
}


@function_tool()
async def query_firecrawl(
    keyword: str,
    sources: ScientificSource,
    modifiers: Optional[str] = None,
    max_results_per_source: int = 5,
    use_advanced_query: bool = False,
    custom_domain: Optional[str] = None,
    custom_query_format: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search for scientific literature using Firecrawl across multiple scientific resources with optimized search phrases.

    This function provides rapid access to scientific publications, preprints, and resources by using
    site-specific search optimizations through Firecrawl. It can search multiple sources in one call
    and format queries appropriately for each source.

    Args:
        keyword (str): The main search keyword or phrase (e.g., "rheumatoid arthritis IL-6")
        sources (Union[ScientificSource, List[ScientificSource]]): One or more scientific sources to search
                Default is PubMed. Can specify multiple sources to search in parallel.
        modifiers (str, optional): Additional search terms to refine results (e.g., "treatment 2023 clinical trial")
        max_results_per_source (int): Maximum number of results to return per source
        use_advanced_query (bool): Whether to use the advanced query template that includes modifiers
        custom_domain (str, optional): Domain to search if using ScientificSource.CUSTOM
        custom_query_format (str, optional): Custom query format if using ScientificSource.CUSTOM

    Returns:
        Dict[str, Any]: Dictionary containing results organized by source, with full result data and metadata

    Examples:
        # Search PubMed for basic keyword
        query_firecrawl("rheumatoid arthritis IL-6")

        # Search multiple sources with modifiers
        query_firecrawl(
            "rheumatoid arthritis IL-6",
            sources=[ScientificSource.PUBMED, ScientificSource.BIORXIV],
            modifiers="treatment clinical trial 2022",
            use_advanced_query=True
        )

        # Search a custom domain with specific format
        query_firecrawl(
            "rheumatoid arthritis",
            sources=ScientificSource.CUSTOM,
            custom_domain="rheumatology-journal.com",
            custom_query_format="rheumatoid arthritis {keyword}"
        )
    """
    firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

    # Normalize sources to a list
    if not isinstance(sources, list):
        sources = [sources]

    results = {}

    for source in sources:
        # Handle custom source
        if source == ScientificSource.CUSTOM:
            if not custom_domain:
                raise ValueError(
                    "custom_domain must be provided when using ScientificSource.CUSTOM"
                )

            domain = custom_domain
            query_format = custom_query_format or "{keyword}"
            query = query_format.format(keyword=keyword)

        # Handle predefined sources
        else:
            if source not in SOURCE_CONFIG:
                raise ValueError(f"Unknown scientific source: {source}")

            config = SOURCE_CONFIG[source]
            domain = config["domain"]

            if use_advanced_query and modifiers:
                query_template = config["advanced_template"]
                query = query_template.format(keyword=keyword, modifiers=modifiers)
            else:
                query_template = config["query_template"]
                query = query_template.format(keyword=keyword)

        # Run the search
        search_params = {
            "query": f"site:{domain} {query}",
            "params": {"pageOptions": {"limit": max_results_per_source}},
        }

        try:
            source_results = firecrawl.search(**search_params)
            results[source.value if hasattr(source, "value") else str(source)] = (
                source_results
            )
        except Exception as e:
            results[source.value if hasattr(source, "value") else str(source)] = {
                "error": str(e),
                "data": [],
            }

    return results
