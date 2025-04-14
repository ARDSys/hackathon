import requests
from typing import Optional, Union, Dict, Any, List
from dataclasses import dataclass
from typing import List, Optional
from datetime import date
import pprint
from enum import Enum


@dataclass
class Message:
    status: str
    category: Optional[str] = None
    interval: Optional[str] = None
    cursor: Optional[int] = None
    count: Optional[int] = None
    count_new_papers: Optional[str] = None
    total: Optional[str] = None

    def __str__(self) -> str:
        result = [f"Status: {self.status}"]
        if self.category:
            result.append(f"Category: {self.category}")
        if self.interval:
            result.append(f"Interval: {self.interval}")
        if self.cursor is not None:
            result.append(f"Cursor: {self.cursor}")
        if self.count is not None:
            result.append(f"Count: {self.count}")
        if self.count_new_papers:
            result.append(f"New papers: {self.count_new_papers}")
        if self.total:
            result.append(f"Total: {self.total}")
        return ", ".join(result)


@dataclass
class Paper:
    title: str
    authors: str
    author_corresponding: str
    author_corresponding_institution: str
    doi: str
    date: date
    version: str
    type: str
    license: str
    category: str
    jatsxml: str
    abstract: str
    published: str
    server: str

    def __str__(self) -> str:
        return (
            f"Title: {self.title}\n"
            f"Authors: {self.authors}\n"
            f"DOI: {self.doi}\n"
            f"Date: {self.date}\n"
            f"Category: {self.category}\n"
            f"Abstract: {self.abstract[:200]}..."
        )


@dataclass
class BioRxivResponse:
    messages: List[Message]
    collection: List[Paper]

    def __str__(self) -> str:
        result = ["=== Messages ==="]
        for msg in self.messages:
            result.append(str(msg))
        result.append("\n=== Papers ===")
        for paper in self.collection:
            result.append(str(paper))
            result.append("-" * 80)
        return "\n".join(result)


class BioRxivAPI:
    BASE_URL = "https://api.biorxiv.org"

    def __init__(self, default_format: str = "json"):
        if default_format not in {"json", "xml", "html", "csv"}:
            raise ValueError("Invalid format. Choose from: json, xml, html, csv.")
        self.default_format = default_format

    def _get(self, endpoint: str, params: dict = None):
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json() if self.default_format == "json" else response.text

    def get_details(
        self,
        server: str,
        interval: Union[str, int],
        cursor: int = 0,
        category: Optional[str] = None,
        doi: Optional[str] = None,
    ):
        if doi:
            endpoint = f"/details/{server}/{doi}/na/{self.default_format}"
        else:
            endpoint = f"/details/{server}/{interval}/{cursor}/{self.default_format}"
        params = {}
        if category:
            params["category"] = category.replace(" ", "_")
        return self._get(endpoint, params)

    def get_publications(
        self,
        server: str,
        interval: Union[str, int],
        cursor: int = 0,
        doi: Optional[str] = None,
    ):
        if doi:
            endpoint = f"/pubs/{server}/{doi}/na/{self.default_format}"
        else:
            endpoint = f"/pubs/{server}/{interval}/{cursor}"
        return self._get(endpoint)

    def get_biorxiv_pubs(self, interval: Union[str, int], cursor: int = 0):
        endpoint = f"/pub/{interval}/{cursor}"
        return self._get(endpoint)

    def get_publisher_pubs(
        self, prefix: str, interval: Union[str, int], cursor: int = 0
    ):
        endpoint = f"/publisher/{prefix}/{interval}/{cursor}"
        return self._get(endpoint)

    def get_summary_statistics(self, interval: str):
        if interval not in {"m", "y"}:
            raise ValueError("Interval must be 'm' or 'y'")
        endpoint = f"/sum/{interval}/{self.default_format}"
        return self._get(endpoint)

    def get_usage_statistics(self, interval: str):
        if interval not in {"m", "y"}:
            raise ValueError("Interval must be 'm' or 'y'")
        endpoint = f"/usage/{interval}/{self.default_format}"
        return self._get(endpoint)

    def get_papers_by_category(
        self,
        server: str,
        category: str,
        interval: Union[str, int] = 100,
        cursor: int = 0,
    ):

        category_param = category.replace(" ", "_")
        if isinstance(interval, int):
            endpoint = f"/details/{server}/{interval}"
        else:
            endpoint = f"/details/{server}/{interval}/{cursor}/{self.default_format}"
        params = {"category": category_param}
        return self._get(endpoint, params)

    def parse_response(self, json_data: dict) -> BioRxivResponse:
        messages = [Message(**msg) for msg in json_data["messages"]]
        # Convert string dates to date objects
        papers = []
        for paper_data in json_data["collection"]:
            paper_data["date"] = date.fromisoformat(paper_data["date"])
            papers.append(Paper(**paper_data))

        response = BioRxivResponse(messages=messages, collection=papers)
        str_response = str(response)
        return str_response


## BIO PORTAL API


import requests
from typing import Optional, Union, Dict


@dataclass
class Links:
    self: str
    ontology: str
    children: str
    parents: str
    descendants: str
    ancestors: str
    instances: str
    tree: str
    notes: str
    mappings: str
    ui: str

    @classmethod
    def from_json(cls, data: dict) -> "Links":
        # Remove @context field as we don't need it
        transformed_data = data.copy()
        transformed_data.pop("@context", None)
        return cls(**transformed_data)


@dataclass
class Context:
    vocab: str
    prefLabel: str
    obsolete: str
    language: str


@dataclass
class SearchResult:
    prefLabel: str
    obsolete: bool
    matchType: str
    ontologyType: str
    provisional: bool
    id: str  # Using id instead of @id since @ is not valid in Python identifiers
    type: str  # Using type instead of @type
    links: Links

    @classmethod
    def from_json(cls, data: dict) -> "SearchResult":
        # Transform @id and @type to id and type
        transformed_data = data.copy()

        transformed_data.pop("@context", None)  # Remove @context field
        transformed_data.pop("synonym", None)  # Remove @vocab field
        transformed_data.pop("cui", None)  # Remove @prefLabel field
        if "@id" in transformed_data:
            transformed_data["id"] = transformed_data.pop("@id")
        if "@type" in transformed_data:
            transformed_data["type"] = transformed_data.pop("@type")

        # Create Links object from nested dict
        if "links" in transformed_data:
            transformed_data["links"] = Links.from_json(transformed_data["links"])

        return cls(**transformed_data)


@dataclass
class SearchResponse:
    page: int
    pageCount: int
    totalCount: int
    prevPage: Optional[int]
    nextPage: Optional[int]
    links: Dict[str, Optional[str]]
    collection: List[SearchResult]


class BioPortalAPI:

    BASE_URL = "https://data.bioontology.org"

    def __init__(self, api_key: str, default_format: str = "json"):
        if default_format not in {"json", "jsonp", "xml"}:
            raise ValueError("Invalid format. Choose from: json, jsonp, xml")
        self.api_key = api_key
        self.default_format = default_format
        self.headers = {"Authorization": f"apikey token={api_key}"}

    def _get(self, endpoint: str, params: dict = None):
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json() if self.default_format == "json" else response.text

    def search(
        self,
        query: str,
        ontologies: Optional[str] = None,
        require_exact_match: bool = False,
        suggest: bool = False,
        include_views: bool = False,
        require_definitions: bool = False,
        include_properties: bool = False,
        include_obsolete: bool = False,
        cuis: Optional[str] = None,
        semantic_types: Optional[str] = None,
        page: int = 1,
        pagesize: int = 50,
        language: str = "en",
    ):
        endpoint = "/search"
        params = {
            "q": query,
            "require_exact_match": str(require_exact_match).lower(),
            "suggest": str(suggest).lower(),
            "also_search_views": str(include_views).lower(),
            "require_definitions": str(require_definitions).lower(),
            "also_search_properties": str(include_properties).lower(),
            "also_search_obsolete": str(include_obsolete).lower(),
            "page": page,
            "pagesize": pagesize,
            "language": language,
        }

        if ontologies:
            params["ontologies"] = ontologies
        if cuis:
            params["cui"] = cuis
        if semantic_types:
            params["semantic_types"] = semantic_types

        return self._get(endpoint, params)

    def search_subtree(
        self,
        query: str,
        ontology: str,
        subtree_root_id: str,
        page: int = 1,
        pagesize: int = 50,
    ):
        endpoint = "/search"
        params = {
            "q": query,
            "ontology": ontology,
            "subtree_root_id": subtree_root_id,
            "page": page,
            "pagesize": pagesize,
        }
        return self._get(endpoint, params)

    def search_roots(
        self, query: str, ontologies: str, page: int = 1, pagesize: int = 50
    ):
        endpoint = "/search"
        params = {
            "q": query,
            "ontologies": ontologies,
            "roots_only": "true",
            "page": page,
            "pagesize": pagesize,
        }
        return self._get(endpoint, params)

    def search_properties(
        self,
        query: str,
        ontologies: Optional[str] = None,
        require_exact_match: bool = False,
        include_views: bool = False,
        require_definitions: bool = False,
        property_types: Optional[str] = None,
        page: int = 1,
        pagesize: int = 50,
    ):
        endpoint = "/property_search"
        params = {
            "q": query,
            "require_exact_match": str(require_exact_match).lower(),
            "also_search_views": str(include_views).lower(),
            "require_definitions": str(require_definitions).lower(),
            "page": page,
            "pagesize": pagesize,
        }

        if ontologies:
            params["ontologies"] = ontologies
        if property_types:
            params["property_types"] = property_types

        return self._get(endpoint, params)

    def annotate(
        self,
        text: str,
        ontologies: Optional[List[str]] = None,
        semantic_types: Optional[List[str]] = None,
        expand_semantic_types_hierarchy: bool = False,
        expand_class_hierarchy: bool = False,
        class_hierarchy_max_level: int = 0,
        expand_mappings: bool = False,
        stop_words: Optional[List[str]] = None,
        minimum_match_length: Optional[int] = None,
        exclude_numbers: bool = False,
        whole_word_only: bool = True,
        exclude_synonyms: bool = False,
        longest_only: bool = False,
    ) -> Dict:
        """
        Examine text input and return relevant classes using the Annotator API.

        Args:
            text (str): The text to annotate
            ontologies (List[str], optional): List of ontology IDs to restrict the annotation
            semantic_types (List[str], optional): List of semantic types to restrict the annotation
            expand_semantic_types_hierarchy (bool): Whether to include children of specified semantic types
            expand_class_hierarchy (bool): Whether to include ancestors when performing annotation
            class_hierarchy_max_level (int): Depth of hierarchy to use for annotation
            expand_mappings (bool): Whether to use manual mappings in annotation
            stop_words (List[str], optional): Custom stop words to use
            minimum_match_length (int, optional): Minimum length for matches
            exclude_numbers (bool): Whether to exclude numbers from annotation
            whole_word_only (bool): Whether to match whole words only
            exclude_synonyms (bool): Whether to exclude synonyms from results
            longest_only (bool): Whether to return only the longest match for a phrase

        Returns:
            Dict: The annotation results
        """
        endpoint = "/annotator"
        params = {
            "text": text,
            "expand_semantic_types_hierarchy": str(
                expand_semantic_types_hierarchy
            ).lower(),
            "expand_class_hierarchy": str(expand_class_hierarchy).lower(),
            "class_hierarchy_max_level": class_hierarchy_max_level,
            "expand_mappings": str(expand_mappings).lower(),
            "exclude_numbers": str(exclude_numbers).lower(),
            "whole_word_only": str(whole_word_only).lower(),
            "exclude_synonyms": str(exclude_synonyms).lower(),
            "longest_only": str(longest_only).lower(),
        }

        if ontologies:
            params["ontologies"] = ",".join(ontologies)
        if semantic_types:
            params["semantic_types"] = ",".join(semantic_types)
        if stop_words:
            params["stop_words"] = ",".join(stop_words)
        if minimum_match_length is not None:
            params["minimum_match_length"] = minimum_match_length

        return self._get(endpoint, params)

    def recommend(
        self,
        input_text: str,
        input_type: int = 1,
        output_type: int = 1,
        max_elements_set: int = 3,
        weight_coverage: float = 0.55,
        weight_acceptance: float = 0.15,
        weight_detail: float = 0.15,
        weight_specialization: float = 0.15,
        ontologies: Optional[List[str]] = None,
    ) -> Dict:
        """
        Get ontology recommendations based on input text or keywords.

        Args:
            input_text (str): Text or comma-separated keywords to get recommendations for
            input_type (int): 1 for text, 2 for comma-separated keywords
            output_type (int): 1 for ranked list of ontologies, 2 for ranked list of ontology sets
            max_elements_set (int): Maximum number of ontologies per set (for output_type=2)
            weight_coverage (float): Weight for ontology coverage criterion (0-1)
            weight_acceptance (float): Weight for ontology acceptance criterion (0-1)
            weight_detail (float): Weight for ontology detail criterion (0-1)
            weight_specialization (float): Weight for ontology specialization criterion (0-1)
            ontologies (List[str], optional): List of ontology IDs to restrict recommendations to

        Returns:
            Dict: The recommendation results

        Raises:
            ValueError: If weight parameters are not in range [0,1] or if input/output types are invalid
        """
        # Validate input parameters
        if not (
            0 <= weight_coverage <= 1
            and 0 <= weight_acceptance <= 1
            and 0 <= weight_detail <= 1
            and 0 <= weight_specialization <= 1
        ):
            raise ValueError("Weight parameters must be in range [0,1]")

        if input_type not in {1, 2}:
            raise ValueError("input_type must be 1 (text) or 2 (keywords)")

        if output_type not in {1, 2}:
            raise ValueError(
                "output_type must be 1 (ontology list) or 2 (ontology sets)"
            )

        if max_elements_set not in {2, 3, 4}:
            raise ValueError("max_elements_set must be 2, 3, or 4")

        endpoint = "/recommender"
        params = {
            "input": input_text,
            "input_type": input_type,
            "output_type": output_type,
            "max_elements_set": max_elements_set,
            "wc": weight_coverage,
            "wa": weight_acceptance,
            "wd": weight_detail,
            "ws": weight_specialization,
        }

        if ontologies:
            params["ontologies"] = ",".join(ontologies)

        return self._get(endpoint, params)

    def get_ontologies_from_search_result(self, result: str):
        """
        Get ontologies from the search result.
        """
        if self.default_format == "json":
            return [item["prefLabel"] for item in result["collection"]]
        else:
            raise ValueError("Unsupported format. Only JSON is supported.")

    def parse(self, json_data: dict) -> SearchResponse:
        # Transform the top-level data for SearchResponse
        top_level_data = json_data.copy()

        # Create SearchResult objects with transformed data
        collection = [SearchResult.from_json(item) for item in json_data["collection"]]

        # Remove collection from top level data as we'll set it after creating SearchResponse
        top_level_data.pop("collection", None)

        # Create SearchResponse and set collection
        response = SearchResponse(**top_level_data)
        response.collection = collection
        return response


## OPEN TARGETS

import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass
from typing import List


@dataclass
class OpenTargetsResponse:
    data: Dict[str, Any]


class OpenTargetsAPI:
    """
    A wrapper class for the Open Targets Platform GraphQL API.
    """

    BASE_URL = "https://api.platform.opentargets.org/api/v4/graphql"

    def __init__(self):
        self.session = requests.Session()

    def _post_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Execute a GraphQL query and return the response.

        Args:
            query (str): The GraphQL query string
            variables (Dict, optional): Variables for the GraphQL query

        Returns:
            Dict: The JSON response from the API
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = self.session.post(self.BASE_URL, json=payload)
        response.raise_for_status()
        return response.json()

    def get_target_info(self, ensembl_id: str) -> OpenTargetsResponse:
        """
        Get information about a target by its Ensembl ID.

        Args:
            ensembl_id (str): The Ensembl ID of the target

        Returns:
            OpenTargetsResponse: The parsed API response
        """
        query = """
        query target($ensemblId: String!){
            target(ensemblId: $ensemblId){
                id
                approvedSymbol
                biotype
                geneticConstraint {
                    constraintType
                    exp
                    obs
                    score
                    oe
                    oeLower
                    oeUpper
                }
                tractability {
                    label
                    modality
                    value
                }
            }
        }
        """
        variables = {"ensemblId": ensembl_id}
        response = self._post_query(query, variables)
        return OpenTargetsResponse(data=response)

    def get_disease_info(self, disease_id: str) -> OpenTargetsResponse:
        """
        Get information about a disease by its ID.

        Args:
            disease_id (str): The disease ID

        Returns:
            OpenTargetsResponse: The parsed API response
        """
        query = """
        query disease($diseaseId: String!){
            disease(efoId: $diseaseId){
                id
                name
                description
                therapeuticAreas {
                    id
                    name
                }
            }
        }
        """
        variables = {"diseaseId": disease_id}
        response = self._post_query(query, variables)
        return OpenTargetsResponse(data=response)

    def get_target_disease_associations(self, ensembl_id: str) -> OpenTargetsResponse:
        """
        Get diseases associated with a target by its Ensembl ID.

        Args:
            ensembl_id (str): The Ensembl ID of the target

        Returns:
            OpenTargetsResponse: The parsed API response containing associated diseases
        """
        query = """
        query associatedDiseases($ensemblId: String!) {
            target(ensemblId: $ensemblId) {
                id
                approvedSymbol
                associatedDiseases {
                    count
                    rows {
                        disease {
                            id
                            name
                        }
                        datasourceScores {
                            id
                            score
                        }
                    }
                }
            }
        }
        """
        variables = {"ensemblId": ensembl_id}
        response = self._post_query(query, variables)
        return OpenTargetsResponse(data=response)

    def get_disease_target_associations(self, disease_id: str) -> OpenTargetsResponse:
        """
        Get targets associated with a disease by its ID.

        Args:
            disease_id (str): The disease ID

        Returns:
            OpenTargetsResponse: The parsed API response containing associated targets
        """
        query = """
        query associatedTargets($diseaseId: String!) {
            disease(efoId: $diseaseId) {
                id
                name
                associatedTargets {
                    count
                    rows {
                        target {
                            id
                            approvedSymbol
                            approvedName
                        }
                        score
                    }
                }
            }
        }
        """
        variables = {"diseaseId": disease_id}
        response = self._post_query(query, variables)
        return OpenTargetsResponse(data=response)

    def get_drug_info(self, drug_id: str) -> OpenTargetsResponse:
        """
        Get information about a drug by its ID.

        Args:
            drug_id (str): The drug ID

        Returns:
            OpenTargetsResponse: The parsed API response
        """
        query = """
        query drug($drugId: String!){
            drug(chemblId: $drugId){
                id
                name
                description
                maximumClinicalTrialPhase
                indications {
                    count
                    rows {
                        disease {
                            id
                            name
                        }
                        phase
                    }
                }
            }
        }
        """
        variables = {"drugId": drug_id}
        response = self._post_query(query, variables)
        return OpenTargetsResponse(data=response)

    def search(
        self, query_string: str, search_type: Optional[str] = None
    ) -> OpenTargetsResponse:
        """
        Search across all entities in the Platform.

        Args:
            query_string (str): The search query
            search_type (str, optional): Type of entity to search for

        Returns:
            OpenTargetsResponse: The parsed API response
        """
        query = """
        query search($queryString: String!){
            search(queryString: $queryString){
                total
                hits {
                    id
                    name
                    description
                    entity
                }
            }
        }
        """
        variables = {"queryString": query_string}
        response = self._post_query(query, variables)
        return OpenTargetsResponse(data=response)


## EUROPE PMC


class EuropePMCAPI:
    """
    Klasa reprezentująca opakowanie (wrapper) dla Europe PMC RESTful Web Service.
    Umożliwia wykonywanie zapytań wyszukiwania artykułów i preprintów.
    """

    def __init__(
        self, base_url="https://www.ebi.ac.uk/europepmc/webservices/rest", format="json"
    ):
        """
        Inicjalizacja podstawowych parametrów API.

        :param base_url: Bazowy URL serwisu Europe PMC.
        :param format: Format odpowiedzi (np. 'json', 'xml', 'dc').
        """
        self.base_url = base_url
        self.format = format

    def search(self, query, result_type="lite", pageSize=25, page=1, **kwargs):
        """
        Metoda wyszukiwania publikacji na podstawie podanego zapytania.

        :param query: Ciąg znaków będący zapytaniem wyszukiwania, zgodnym ze składnią Europe PMC.
        :param result_type: Określa rodzaj zwracanych wyników:
                            - 'idlist': lista ID i źródeł,
                            - 'lite': podstawowe metadane (domyślnie),
                            - 'core': pełna metadane publikacji.
        :param pageSize: Liczba wyników na jedną stronę (domyślnie 25).
        :param page: Numer strony wyników (domyślnie 1).
        :param kwargs: Dodatkowe parametry (np. sortowanie poprzez "sort_date:y" lub "sort_cited:y").
        :return: Słownik zawierający zdeserializowaną odpowiedź w formacie JSON lub surowy tekst,
                 zależnie od ustawionego formatu.
        :raises: requests.HTTPError w przypadku niepowodzenia zapytania.
        """
        params = {
            "query": query,
            "resultType": result_type,
            "pageSize": pageSize,
            "page": page,
            "format": self.format,
        }
        # Aktualizacja parametrów dodatkowymi argumentami (np. sortowanie)
        params.update(kwargs)

        # Konstruowanie pełnego adresu URL dla metody search
        url = f"{self.base_url}/search"
        response = requests.get(url, params=params)
        response.raise_for_status()  # Rzuca wyjątek, jeśli wystąpił błąd HTTP

        if self.format.lower() == "json":
            return response.json()
        else:
            return response.text


import random
import time
import urllib.error
import urllib.request

from langchain_community.utilities.pubmed import PubMedAPIWrapper


class PubMedTool(PubMedAPIWrapper):
    def retrieve_article(self, uid: str, webenv: str) -> dict:
        url = (
            self.base_url_efetch
            + "db=pubmed&retmode=xml&id="
            + uid
            + "&webenv="
            + webenv
        )
        if self.api_key != "":
            url += f"&api_key={self.api_key}"

        retry = 0
        while True:
            try:
                result = urllib.request.urlopen(url)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and retry < self.max_retry:
                    # Too Many Requests errors
                    # wait for an exponentially increasing amount of time
                    sleep_time_random = random.uniform(0.5, 1.5)
                    sleep_time = self.sleep_time + sleep_time_random
                    print(  # noqa: T201
                        f"Too Many Requests, waiting for {sleep_time:.2f} seconds..."
                    )
                    time.sleep(sleep_time)
                    self.sleep_time *= 2
                    retry += 1
                else:
                    raise e

        xml_text = result.read().decode("utf-8")
        text_dict = self.parse(xml_text)
        return self._parse_article(uid, text_dict)


## NCBI PUBMED

from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import requests


@dataclass
class NCBISearchResponse:
    """Class for representing NCBI E-Search API responses"""

    count: int
    retmax: int
    retstart: int
    query_key: Optional[str]
    webenv: Optional[str]
    ids: List[str]
    translation_set: List[Dict[str, str]]
    raw_data: Dict[str, Any]


class NCBIDatabase(Enum):
    """Supported NCBI databases"""

    PUBMED = "pubmed"
    PMC = "pmc"
    NUCLEOTIDE = "nucleotide"
    PROTEIN = "protein"
    GENE = "gene"
    NLM_CATALOG = "nlmcatalog"


class DateType(Enum):
    """Supported date types for NCBI searches"""

    MODIFICATION_DATE = "mdat"
    PUBLICATION_DATE = "pdat"
    ENTREZ_DATE = "edat"


class SortOrder(Enum):
    """Sort orders for PubMed results"""

    PUBLICATION_DATE = "pub_date"
    AUTHOR = "Author"
    JOURNAL_NAME = "JournalName"
    RELEVANCE = "relevance"


@dataclass
class NCBIFetchResponse:
    """Class for representing NCBI E-Fetch API responses"""

    content: str
    raw_response: Any


class RetMode(Enum):
    """Supported return modes for NCBI EFetch"""

    TEXT = "text"
    XML = "xml"
    ASN1 = "asn.1"
    JSON = "json"


class RetType(Enum):
    """Supported return types for PubMed database"""

    ABSTRACT = "abstract"
    MEDLINE = "medline"
    FULL = "full"
    UILIST = "uilist"

    @classmethod
    def for_database(cls, db: NCBIDatabase) -> List[str]:
        """Get valid return types for a specific database"""
        return {
            NCBIDatabase.PUBMED: ["abstract", "medline", "full", "uilist"],
            NCBIDatabase.NUCLEOTIDE: ["fasta", "gb", "gbc", "gbwithparts"],
            NCBIDatabase.PROTEIN: ["fasta", "gp", "acc", "seqid"],
        }.get(db, [])


class ComplexityLevel(Enum):
    """Complexity levels for sequence data retrieval"""

    ENTIRE_BLOB = "0"
    BIOSEQ = "1"
    MINIMAL_BIOSEQ_SET = "2"
    MINIMAL_NUC_PROT = "3"
    MINIMAL_PUB_SET = "4"


class NCBISearchAPI:
    """
    A wrapper for the NCBI E-Search API.
    Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    def __init__(
        self,
        api_key: Optional[str] = None,
        tool: str = "python_ncbi_wrapper",
        email: Optional[str] = None,
    ):
        """
        Initialize the NCBI Search API wrapper.

        Args:
            api_key: Optional NCBI API key for higher rate limits
            tool: Name of the tool making the request
            email: Email of the user making the request
        """
        self.api_key = api_key
        self.tool = tool
        self.email = email
        self.session = requests.Session()

    def search(
        self,
        term: str,
        db: NCBIDatabase = NCBIDatabase.PUBMED,
        use_history: bool = False,
        webenv: Optional[str] = None,
        query_key: Optional[str] = None,
        retstart: int = 0,
        retmax: int = 20,
        retmode: str = "json",
        sort: Optional[SortOrder] = None,
        field: Optional[str] = None,
        date_type: Optional[DateType] = None,
        rel_date: Optional[int] = None,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
        id_type: Optional[str] = None,
    ) -> NCBISearchResponse:
        """
        Search NCBI databases using the E-Search API.

        Args:
            term: Search query
            db: NCBI database to search
            use_history: Whether to use NCBI History server
            webenv: Web environment string from previous search
            query_key: Query key from previous search
            retstart: First record to retrieve (for pagination)
            retmax: Maximum number of records to retrieve
            retmode: Return format ('json' or 'xml')
            sort: Sort order for results
            field: Field to restrict search to
            date_type: Type of date to filter by
            rel_date: Return only results from last N days
            min_date: Start date for date range (YYYY/MM/DD)
            max_date: End date for date range (YYYY/MM/DD)
            id_type: Type of IDs to return (for sequence databases)

        Returns:
            NCBISearchResponse object containing search results
        """
        params = {
            "db": db.value,
            "term": term,
            "retmode": retmode,
            "retstart": retstart,
            "retmax": retmax,
        }

        # Add optional parameters
        if use_history:
            params["usehistory"] = "y"
        if webenv:
            params["WebEnv"] = webenv
        if query_key:
            params["query_key"] = query_key
        if sort:
            params["sort"] = sort.value
        if field:
            params["field"] = field
        if date_type:
            params["datetype"] = date_type.value
        if rel_date:
            params["reldate"] = rel_date
        if min_date and max_date:
            params["mindate"] = min_date
            params["maxdate"] = max_date
        if id_type:
            params["idtype"] = id_type
        if self.api_key:
            params["api_key"] = self.api_key
        if self.tool:
            params["tool"] = self.tool
        if self.email:
            params["email"] = self.email

        response = self.session.get(self.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        return self._parse_response(data)

    def _parse_response(self, data: Dict[str, Any]) -> NCBISearchResponse:
        """Parse the JSON response from NCBI into a NCBISearchResponse object."""
        esearch_result = data["esearchresult"]
        return NCBISearchResponse(
            count=int(esearch_result.get("count", 0)),
            retmax=int(esearch_result.get("retmax", 0)),
            retstart=int(esearch_result.get("retstart", 0)),
            query_key=esearch_result.get("querykey"),
            webenv=esearch_result.get("webenv"),
            ids=esearch_result.get("idlist", []),
            translation_set=esearch_result.get("translationset", []),
            raw_data=data,
        )

    def fetch(
        self,
        ids: Union[str, List[str]],
        db: NCBIDatabase = NCBIDatabase.PUBMED,
        retmode: RetMode = RetMode.TEXT,
        rettype: Optional[str] = None,
        retstart: int = 0,
        retmax: int = 20,
        strand: Optional[str] = None,
        seq_start: Optional[int] = None,
        seq_stop: Optional[int] = None,
        complexity: Optional[ComplexityLevel] = None,
        webenv: Optional[str] = None,
        query_key: Optional[str] = None,
    ) -> NCBIFetchResponse:
        """
        Fetch records from NCBI databases using the E-Fetch API.

        Args:
            ids: Single ID or list of IDs to fetch (ignored if using webenv/query_key)
            db: NCBI database to fetch from
            retmode: Return mode (text, xml, asn.1, json)
            rettype: Return type (varies by database, e.g. abstract, medline for PubMed)
            retstart: First record to retrieve (for pagination)
            retmax: Maximum number of records to retrieve
            strand: DNA strand to retrieve (1=plus, 2=minus)
            seq_start: First sequence base to retrieve
            seq_stop: Last sequence base to retrieve
            complexity: Data content complexity level for sequences
            webenv: Web environment from previous search
            query_key: Query key from previous search

        Returns:
            NCBIFetchResponse containing the fetched records

        Raises:
            ValueError: If invalid parameters are provided
            requests.HTTPError: If the API request fails
        """
        # Base parameters
        params = {
            "db": db.value,
            "retmode": retmode.value,
            "retstart": retstart,
            "retmax": retmax,
        }

        # Add IDs if provided
        if ids:
            if isinstance(ids, list):
                params["id"] = ",".join(str(id) for id in ids)
            else:
                params["id"] = str(ids)

        # Add optional parameters
        if rettype:
            valid_types = RetType.for_database(db)
            if rettype not in valid_types:
                raise ValueError(
                    f"Invalid rettype '{rettype}' for database {db.value}. "
                    f"Valid values are: {', '.join(valid_types)}"
                )
            params["rettype"] = rettype

        if webenv and query_key:
            params["WebEnv"] = webenv
            params["query_key"] = query_key
        elif bool(webenv) != bool(query_key):
            raise ValueError("Both webenv and query_key must be provided together")

        # Sequence-specific parameters
        if db in [NCBIDatabase.NUCLEOTIDE, NCBIDatabase.PROTEIN]:
            if strand:
                if strand not in ["1", "2"]:
                    raise ValueError("strand must be '1' (plus) or '2' (minus)")
                params["strand"] = strand

            if seq_start is not None:
                params["seq_start"] = seq_start
            if seq_stop is not None:
                params["seq_stop"] = seq_stop
            if complexity:
                params["complexity"] = complexity.value

        # Add API key and tool info
        if self.api_key:
            params["api_key"] = self.api_key
        if self.tool:
            params["tool"] = self.tool
        if self.email:
            params["email"] = self.email

        # Make request
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        response = self.session.get(url, params=params)
        response.raise_for_status()

        # Return response based on retmode
        if retmode == RetMode.JSON:
            return NCBIFetchResponse(content=response.json(), raw_response=response)
        else:
            return NCBIFetchResponse(content=response.text, raw_response=response)
