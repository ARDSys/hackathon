from agents import function_tool
from semanticscholar import SemanticScholar

from biohack_attack.other.api_wrappers import (
    BioRxivAPI,
    EuropePMCAPI,
    PubMedTool,
)


@function_tool
def get_biorxiv_papers_by_category(keyword: str) -> str:
    """Fetch Biorxiv papers by keyword. It returns

    Args:
        keyword: The keyword to search for in Biorxiv papers.
    Returns:
        str: The strucuted response form the Biorxiv API.
    """
    bioarxiv = BioRxivAPI()

    response = bioarxiv.get_papers_by_category(server="biorxiv", category=keyword)
    if response.status_code != 200:
        raise Exception(f"Error fetching papers: {response.status_code}")

    parsed_response = bioarxiv.parse_response(response)

    return parsed_response


@function_tool
def get_semanticscholar_papers_by_keyword(keyword: str) -> str:
    """Fetch Semantic Scholar papers by keyword. It returns

    Args:
        keyword: The keyword to search for in Semantic Scholar papers.
    Returns:
        str: The strucuted response form the Semantic Scholar API.
    """

    sch = SemanticScholar()
    papers = sch.search_paper(keyword=keyword)

    parsed_papers = []

    for paper in papers:
        paper_dict = {
            "title": paper.title,
            "year": paper.year,
            "abstract": paper.abstract,
            "authors": [author.name for author in paper.authors],
            "fieldsOfStudy": paper.fieldsOfStudy,
            "venue": paper.venue,
        }
        parsed_papers.append(paper_dict)

    return parsed_papers


@function_tool
def get_europe_pmc_papers_by_keyword(keyword: str) -> str:
    """Fetch Semantic Scholar papers by keyword. It returns

    Args:
        keyword: The keyword to search for in Semantic Scholar papers.
    Returns:
        str: The strucuted response form the Semantic Scholar API.
    """

    europePMC = EuropePMCAPI()
    response = europePMC.search(query=keyword, result_type="core", pageSize=100)
    if response.status_code != 200:
        raise Exception(f"Error fetching papers: {response.status_code}")

    parsed_response = []

    for item in response["resultList"]["result"]:
        parsed_item = {
            "title": item["title"],
            "abstract": item.get("abstractText", "<NO ABSTRACT>"),
            "pubYear": item["pubYear"],
            "doi": item["doi"],
            "authorString": item.get("authorString", "<NO AUTHOR>"),
        }
        parsed_response.append(parsed_item)

    return response


@function_tool
def get_pubmed_papers_by_keyword(keyword: str) -> str:
    """Fetch PubMed papers by keyword. It returns

    Args:
        keyword: The keyword to search for in PubMed papers.
    Returns:
        str: The strucuted response form the PubMed API.
    """

    pubmed = PubMedTool(
        api_key="b3ec3bcde8b0b257216261f910e1f431d608",
        top_k_results=10,
        MAX_QUERY_LENGTH=2000,
        max_retry=5,
        doc_content_chars_max=10_000,
    )

    response = pubmed.run(keyword)
    if response.status_code != 200:
        raise Exception(f"Error fetching papers: {response.status_code}")

    return response
