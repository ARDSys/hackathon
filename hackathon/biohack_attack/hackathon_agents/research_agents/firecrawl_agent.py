from typing import List, Optional

from agents import Agent, ModelSettings
from pydantic import BaseModel, Field

from biohack_attack.hackathon_agents.research_agents.models import UnstructuredSource
from biohack_attack.hackathon_agents.research_agents.tools.firecrawl_tool import (
    query_firecrawl,
)
from biohack_attack.model_factory import ModelFactory, ModelType
from biohack_attack.tools.hetionet import query_hetionet


class FirecrawlSearchInput(BaseModel):
    """Input parameters for Firecrawl search."""

    keyword: str = Field(description="Main search keyword or phrase")
    sources: List[str] = Field(
        default=["pubmed"],
        description="Scientific sources to search (e.g., pubmed, biorxiv, nature, etc.)",
    )
    modifiers: Optional[str] = Field(
        None,
        description="Additional search terms to refine results (e.g., 'treatment 2023 clinical trial')",
    )
    max_results_per_source: int = Field(
        default=5, description="Maximum number of results to return per source"
    )
    use_advanced_query: bool = Field(
        default=False, description="Whether to use advanced query format with modifiers"
    )


# Updated Firecrawl agent with more comprehensive description and capability
firecrawl_agent = Agent(
    name="Scientific Web Search Agent",
    instructions="""
    You are a specialized scientific literature search agent that uses Firecrawl to efficiently search 
    multiple scientific resources. Your goal is to find the most relevant publications, preprints, 
    and scientific content based on the researcher's query.

    ## CAPABILITIES
    You can search across multiple scientific sites simultaneously, including:
    - PubMed (pubmed.ncbi.nlm.nih.gov): For peer-reviewed medical literature
    - bioRxiv (biorxiv.org): For biology preprints
    - medRxiv (medrxiv.org): For medical preprints
    - NIH (nih.gov): For government research
    - Nature (nature.com): For high-impact research
    - Science (science.org): For high-impact research
    - Cell (cell.com): For cell biology research
    - The Lancet (thelancet.com): For medical research
    - BMJ (bmj.com): For medical research
    - NEJM (nejm.org): For medical research
    - Frontiers (frontiersin.org): For open-access research
    - PLOS (plos.org): For open-access research
    - WHO (who.int): For global health data
    - CDC (cdc.gov): For disease control research

    ## YOUR ROLE
    1. When given a keyword, determine which scientific sources would be most relevant
    2. Construct effective search queries with appropriate modifiers
    3. Determine whether to use basic or advanced search formats
    4. Return the results in a structured format with justification

    ## BEST PRACTICES
    - For general queries, search across multiple relevant sources
    - For specific disease mechanisms, include both PubMed and preprint servers
    - Use modifiers effectively to refine results (e.g., add "treatment", "mechanism", "clinical trial")
    - For cutting-edge research, prioritize preprint servers
    - For established medical knowledge, prioritize medical journals

    Remember to format your responses following the UnstructuredSource schema.
    """,
    model=ModelFactory.build_model(ModelType.OPENAI),
    tools=[
        query_firecrawl,
        query_hetionet,
    ],
    output_type=UnstructuredSource,
    model_settings=ModelSettings(tool_choice="required"),
)
