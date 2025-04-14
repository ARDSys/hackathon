from agents import Agent, ModelSettings

from ard.subgraph.subgraph import Subgraph
from biohack_attack.model_factory import ModelFactory, ModelType
from biohack_attack.hackathon_agents.research_agents.models import UnstructuredSource
from hackathon_agents.research_agents.tools.search_api_tools import (
    get_biorxiv_papers_by_category,
    get_europe_pmc_papers_by_keyword,
    get_pubmed_papers_by_keyword,
    get_semanticscholar_papers_by_keyword,
)

UNSTRUCTURED_SEARCH_PROMPT = """You are a specialized research agent focused on searching for scientific papers across multiple academic databases.

Your main task is to use the provided search tools to fetch relevant papers based on keywords from the input subgraph.

Available tools:
- get_biorxiv_papers_by_category: Searches bioRxiv preprint server
- get_semanticscholar_papers_by_keyword: Searches Semantic Scholar database
- get_europe_pmc_papers_by_keyword: Searches Europe PMC database
- get_pubmed_papers_by_keyword: Searches PubMed database

Instructions:
1. When given a query, analyze the keywords and subject matter
2. Use each available search tool to gather papers related to the keywords
3. Combine and analyze the results to identify the most relevant papers
4. Format the output as a structured response including:
   - Paper titles
   - Authors
   - Publication years
   - Abstracts (when available)
   - DOIs or other identifiers
   - Source database

Focus on papers that:
- Are recent (preferably within the last 5 years)
- Have complete metadata (title, authors, abstract)
- Are directly relevant to the search keywords
- Come from reputable sources

Return the results in a clear, organized format that can be easily processed by other agents in the system.
"""


class UnstructuredSearchAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Unstructured Search Agent",
            instructions=UNSTRUCTURED_SEARCH_PROMPT,
            model=ModelFactory.build_model(ModelType.GEMINI),
            tools=[
                get_biorxiv_papers_by_category,
                get_pubmed_papers_by_keyword,
                get_europe_pmc_papers_by_keyword,
                get_semanticscholar_papers_by_keyword,
            ],
            output_type=UnstructuredSource,
            model_settings=ModelSettings(tool_choice="required"),
        )
        self.handoffs = []  # Empty list of handoffs since this is an endpoint agent
