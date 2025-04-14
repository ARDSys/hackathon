from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import InjectedState
from langchain_core.tools import InjectedToolCallId
from typing import Annotated, Dict, Any

from .backends.UniProtAPIWrapper import UniProtAPIWrapper
from .backends.UniProtQueryTool import parse_uniprot_entry
from .backends.EnsemblApiManager import EnsemblApiClient
from .backends.BioRxivAPIManager import BioRxivAPIManager
from .backends.EuropePMCApiManager import EuropePMCAPIManager

# Initialize UniProt wrapper
api_wrapper = UniProtAPIWrapper()
# Initialize BioRxiv API manager
biorxiv_api = BioRxivAPIManager()
# Initialize Ensembl API client
ensembl_api = EnsemblApiClient()
#EuropePMC API

@tool("query_uniprot", parse_docstring=True)
def query_uniprot(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Searches UniProt for information on a gene or protein. Best used when a node is a gene or biological process involving proteins or enzymes.

    Args:
        query (str): A gene or protein name (e.g., "BRCA1", "IL6").

    Returns:
        dict: A structured dictionary with UniProt metadata (e.g., definition, synonyms, ontology ID, etc.)
    """
    result = api_wrapper.search(query)

    if not result:
        return {
            "error": f"No UniProt entry found for '{query}'.",
            "ontology_id": None,
            "definition": "No entry found.",
            "synonyms": [],
        }

    parsed = parse_uniprot_entry(result)

    return {
        "definition": parsed.get("function") or parsed.get("protein_name") or "No description available.",
        "ontology_id": parsed.get("accession"),
        "synonyms": parsed.get("gene_names", []),
    }
@tool("biorxiv_search", parse_docstring=True)
def biorxiv_search_by_doi(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Searches BioRxiv for preprints related to a given query.

    Args:
        query (str): A search term or phrase.

    Returns:
        dict: A structured dictionary with metadata about the preprints.
    """
    return biorxiv_api.fetch_details_by_doi(query)
@tool("biorxiv_search_by_date", parse_docstring=True)
def biorxiv_search_by_date_range(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Searches BioRxiv for preprints related to a given query.

    Args:
        query (str): A search term or phrase.

    Returns:
    dict: A structured dictionary with metadata about the preprints.
    """
    start_date = query.get("start_date")
    end_date = query.get("end_date")
    cursor = query.get("cursor", 0)
    category = query.get("category", None)
    format = query.get("format", "json")

    return biorxiv_api.fetch_details_by_date_range(
        start_date, end_date, cursor, category, format
    )
@tool("biorxiv_fetch_publication_details", parse_docstring=True)
def biorxiv_published_details_by_date(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Fetches published article details within a specified date range.

    Args:
        query (dict): A dictionary containing the start and end dates, cursor, and format.

    Returns:
        dict: A structured dictionary with metadata about the preprints.
    """
    start_date = query.get("start_date")
    end_date = query.get("end_date")
    cursor = query.get("cursor", 0)
    format = query.get("format", "json")

    return biorxiv_api.fetch_published_details_by_date(
        start_date, end_date, cursor, format
    )
@tool("biorxiv_fetch_usage_statistics", parse_docstring=True)
def biorxiv_usage_statistics(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Fetches usage statistics for a specific article.

    Args:
        query (str): The DOI of the article.

    Returns:
        dict: A structured dictionary with metadata about the preprints.
    """
    return biorxiv_api.fetch_usage_statistics(query)


@tool("ensembl_get_genetree_by_id", parse_docstring=True)
def ensembl_get_genetree_by_id(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves a gene tree by its ID.

    Args:
        query (str): The ID of the gene tree.

    Returns:
        dict: The JSON response containing the gene tree data.
    """
    return ensembl_api.get_genetree_by_id(query)

@tool("ensembl_get_xrefs_by_symbol", parse_docstring=True)
def ensembl_get_xrefs_by_symbol(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves all Ensembl objects linked to an external symbol.

    Args:
        query (dict): A dictionary containing the species name and symbol.

    Returns:
        dict: The JSON response containing the linked Ensembl objects.
    """
    species = query.get("species")
    symbol = query.get("symbol")
    return ensembl_api.get_xrefs_by_symbol(species, symbol)

@tool("ensembl_get_assembly_info", parse_docstring=True)
def ensembl_get_assembly_info(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves assembly information for a specific species.

    Args:
        query (str): The species name.

    Returns:
        dict: The JSON response containing the assembly information.
    """
    return ensembl_api.get_assembly_info(query)

@tool("ensembl_get_species_list")
def ensembl_get_species_list(
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves a list of all species available in the Ensembl database.

    Returns:
        dict: The JSON response containing the list of species.
    """
    return ensembl_api.get_species_list()

@tool("ensembl_get_sequence_by_id", parse_docstring=True)
def ensembl_get_sequence_by_id(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves the sequence for a specific stable ID.

    Args:
        query (str): The stable ID of the sequence to retrieve.

    Returns:
        dict: The JSON response containing the sequence data.
    """
    return ensembl_api.get_sequence_by_id(query)

@tool("ensembl_get_variation_by_id", parse_docstring=True)
def ensembl_get_variation_by_id(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Fetches variation features by Ensembl ID (e.g., rsID).

    Args:
        query (dict): A dictionary containing the species name and variant ID.

    Returns:
        dict: The JSON response containing the variation features.
    """
    species = query.get("species")
    variant_id = query.get("variant_id")
    return ensembl_api.get_variation_by_id(species, variant_id)

@tool("ensembl_get_phenotype_by_gene", parse_docstring=True)
def ensembl_get_phenotype_by_gene(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves phenotype annotations for a specific gene in a species.

    Args:
        query (dict): A dictionary containing the species name and gene ID.

    Returns:
        dict: The JSON response containing the phenotype annotations.
    """
    species = query.get("species")
    gene_id = query.get("gene_id")
    return ensembl_api.get_phenotype_by_gene(species, gene_id)

@tool("ensembl_get_species_biotypes", parse_docstring=True)
def ensembl_get_species_biotypes(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves all biotypes available for a specific species.

    Args:
        query (str): The species name.

    Returns:
        dict: The JSON response containing the biotypes.
    """
    return ensembl_api.get_biotypes(query)

@tool("ensembl_get_phenotype_by_region", parse_docstring=True)
def ensembl_get_phenotype_by_region(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves phenotype annotations for a specific genomic region.

    Args:
        query (dict): A dictionary containing the species name and genomic region.

    Returns:
        dict: The JSON response containing the phenotype annotations.
    """
    species = query.get("species")
    region = query.get("region")
    return ensembl_api.get_phenotype_by_region(species, region)

@tool("ensembl_get_sequence_by_region", parse_docstring=True)
def ensembl_get_sequence_by_region(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves the sequence for a specific genomic region.

    Args:
        query (dict): A dictionary containing the species name and genomic region.

    Returns:
        dict: The JSON response containing the sequence data.
    """
    species = query.get("species")
    region = query.get("region")
    return ensembl_api.get_sequence_by_region(species, region)
@tool("ensembl_get_vep_by_id", parse_docstring=True)
def ensembl_get_vep_by_id(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves VEP (Variant Effect Predictor) data for a specific variant.

    Args:
        query (dict): A dictionary containing the species name and variant ID.

    Returns:
        dict: The JSON response containing the VEP data.
    """
    species = query.get("species")
    variant_id = query.get("variant_id")
    return ensembl_api.get_vep_by_id(species, variant_id)

@tool("ensembl_get_variant_recoder", parse_docstring=True)
def esembl_get_variant_recorder(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves variant recoder data for a specific variant.

    Args:
        query (dict): A dictionary containing the species name and variant ID.

    Returns:
        dict: The JSON response containing the variant recoder data.
    """
    species = query.get("species")
    variant_id = query.get("variant_id")
    return ensembl_api.get_variant_recoder(species, variant_id)

@tool("ensembl_get_variation_by_pmcid", parse_docstring=True)
def ensembl_get_variation_by_pmcid(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves variation features by PubMed Central ID (PMC ID).

    Args:
        query (dict): A dictionary containing the species name and PMC ID.

    Returns:
        dict: The JSON response containing the variation features.
    """
    species = query.get("species")
    pmcid = query.get("pmcid")
    return ensembl_api.get_variation_by_pmcid(species, pmcid)
@tool("ensembl_get_phenotype_by_pmid", parse_docstring=True)
def get_variation_by_pmid(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves phenotype annotations by PubMed ID (PMID).

    Args:
        query (dict): A dictionary containing the species name and PubMed ID.

    Returns:
        dict: The JSON response containing the phenotype annotations.
    """
    species = query.get("species")
    pmid = query.get("pmid")
    return ensembl_api.get_phenotype_by_pmid(species, pmid)

@tool("eupmcapi_get_article_by_id", parse_docstring=True)
def eupmcapi_get_article_by_id(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves article details by its ID.

    Args:
        query (str): The ID of the article.

    Returns:
        dict: The JSON response containing the article details.
    """

    return EuropePMCAPIManager().get_article(query)
@tool("eupmcapi_get_references", parse_docstring=True)
def eupmcapi_get_references(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves references for a specific article.

    Args:
        query (str): The ID of the article.

    Returns:
        dict: The JSON response containing the references.
    """
    return EuropePMCAPIManager().get_references(query)

@tool("eupmcapi_get_citations", parse_docstring=True)
def eupmcapi_get_citations(
    query: Dict[int, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves citations for a specific article.

    Args:
        query (str): The ID of the article.

    Returns:
        dict: The JSON response containing the citations.
    """
    return EuropePMCAPIManager().get_citations(query)
@tool("eupmcapi_get_db_links", parse_docstring=True)
def eupmcapi_get_db_links(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves database links for a specific article.

    Args:
        query (str): The ID of the article.

    Returns:
        dict: The JSON response containing the database links.
    """
    return EuropePMCAPIManager().get_database_links(query)
@tool("eupmcapi_get_lab_links", parse_docstring=True)
def eupmcapi_get_lab_links(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves lab links for a specific article.

    Args:
        query (str): The ID of the article.

    Returns:
        dict: The JSON response containing the lab links.
    """
    return EuropePMCAPIManager().get_labs_links(query)

@tool("eupmcapi_get_full_text_xml", parse_docstring=True)
def eupmcapi_get_full_text_xml(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> str:
    """
    Retrieves the full text of an article in XML format.

    Args:
        query (Dict[str, Any]): A dictionary containing the query parameters.

    Returns:
        str: The full text in XML format.
    """
    return str(EuropePMCAPIManager().get_full_text_xml(query[0]))

@tool("eupmcapi_get_book_xml", parse_docstring=True)
def eupmcapi_get_book_xml(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> str:
    """
    Retrieves the full text of a book in XML format.

    Args:
        query (str): The ID of the book.

    Returns:
        dict: The JSON response containing the full text.
    """
    return str(EuropePMCAPIManager().get_book_xml(query[0]))
@tool("eupmcapi_get_supplementary_files", parse_docstring=True)
def eupmcapi_get_supplementary_files(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) ->Dict[str, Any]:
    """
    Retrieves supplementary files for a specific article.

    Args:
        query (str): The ID of the article.

    Returns:
        dict: The JSON response containing the supplementary files.
    """
    return EuropePMCAPIManager().get_supplementary_files(query[0])
@tool("eupmcapi_get_evaluations", parse_docstring=True)
def eupmcapi_get_evaluations(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves evaluations for a specific article.

    Args:
        query (str): The ID of the article.

    Returns:
        dict: The JSON response containing the evaluations.
    """
    id = query.get("id")
    if not id:
        return {"error": "ID is required."}
    source = query.get("source")
    return EuropePMCAPIManager().get_evaluations(id, source)

@tool("eupmcapi_custom_search", parse_docstring=True)
def eupmcapi_custom_search(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Performs a custom search on Europe PMC.

    Args:
        query (str): The search term.

    Returns:
        dict: The JSON response containing the search results.
    """
    if not query:
        return {"error": "Query is required."}
    search_query = query.get("query")
    result_type = query.get("result_type")
    sort_by_citations = query.get("sort_by_citations", False or True)
    return EuropePMCAPIManager().custom_search(
        search_query, result_type, sort_by_citations
    )
@tool("eupmcapi_get_most_cited_in period", parse_docstring=True)
def eupmcapi_get_most_cited_in_period(
    query: Dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Retrieves the most cited articles in a specific period.

    Args:
        query (str): The search term.

    Returns:
        dict: The JSON response containing the most cited articles.
    """
    if not query:
        return {"error": "Query is required."}
    search_keyword = query.get("keyword")
    start_year = query.get("start_year")
    end_year = query.get("end_year")
    result_type = "core"
    max_results = 1000

    return EuropePMCAPIManager().get_most_cited_in_period(
        search_keyword, start_year, end_year, result_type, max_results
    )
