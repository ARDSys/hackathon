import asyncio
from typing import Union

from agents import Agent, Runner
from biohack_attack.model_factory import ModelFactory, ModelType
from loguru import logger

from .biorxiv_agent import biorxiv_agent
from .europmc_agent import europe_pmc_agent
from .firecrawl_agent import firecrawl_agent
from .hetionet_agent import hetionet_agent
from .models import (
    DataSource,
    KnowledgeGraph,
    QueriesOutput,
    Query,
    ResearchAgentOutput,
    UnstructuredSource,
)
from .pubmed_agent import pubmed_agent
from .semantic_scholar_agent import semantic_scholar_agent

RESEARCH_AGENT_DISPATCHER_PROMPT = """
You are an expert Graph Expansion System designed to analyze subgraphs and strategically query external data sources to 
enhance the graph's coverage, depth, and utility. Your purpose is to identify missing connections, nodes, and 
relationships that would make the graph more complete and valuable.

Key Responsibilities:
1. Analyze the current subgraph to identify knowledge gaps and areas needing expansion
2. Generate targeted queries with each disease and specific keyword in each query
3. Strategically select appropriate data sources for each query
4. Consider multiple angles and perspectives when querying the same source

Your output should be a list of queries, where each query specifies:
- A targeted keyword or search term
- The most appropriate data source for that specific query
- The rationale for why this query would be valuable for graph expansion

Remember: Quality and relevance are more important than quantity. Each query should have a clear purpose in expanding the graph's knowledge.
"""

research_agent_dispatcher = Agent(
    name="Research Agent Dispatacher",
    instructions=RESEARCH_AGENT_DISPATCHER_PROMPT,
    model=ModelFactory.build_model(ModelType.GEMINI),
    output_type=QueriesOutput,
)


async def perform_queries(queries: QueriesOutput) -> ResearchAgentOutput:
    output = ResearchAgentOutput()

    async def process_query(
        query: Query,
    ) -> tuple[bool, Union[KnowledgeGraph, UnstructuredSource]]:
        try:
            logger.info(
                f"Processing query: {query.keyword} in the data source: {query.data_source}"
            )
            if query.data_source == DataSource.HETIONET:
                result = await Runner.run(hetionet_agent, query.keyword)
                result: KnowledgeGraph = result.final_output_as(KnowledgeGraph)
                return True, result
            elif query.data_source == DataSource.PUBMED:
                result = await Runner.run(pubmed_agent, query.keyword)
                result: UnstructuredSource = result.final_output_as(UnstructuredSource)
                return False, result
            elif query.data_source == DataSource.BIORXIV:
                result = await Runner.run(biorxiv_agent, query.keyword)
                result: UnstructuredSource = result.final_output_as(UnstructuredSource)
                return False, result
            elif query.data_source == DataSource.EUROPE_PMC:
                result = await Runner.run(europe_pmc_agent, query.keyword)
                result: UnstructuredSource = result.final_output_as(UnstructuredSource)
                return False, result
            elif query.data_source == DataSource.SEMANTIC_SCHOLAR:
                result = await Runner.run(semantic_scholar_agent, query.keyword)
                result: UnstructuredSource = result.final_output_as(UnstructuredSource)
                return False, result
            elif query.data_source == DataSource.FIRECRAWL:
                result = await Runner.run(firecrawl_agent, query.keyword)
                result: UnstructuredSource = result.final_output_as(UnstructuredSource)
                return False, result
        except Exception as e:
            print(
                f"Error processing query {query.keyword} from {query.data_source}: {str(e)}"
            )
            return None, None

    # Run all queries concurrently and collect results
    results = await asyncio.gather(*[process_query(query) for query in queries.queries])

    # Process results after all queries are complete
    for is_graph, result in results:
        if result is None:  # Skip failed queries
            continue
        if is_graph:
            output.graphs.append(result)
        else:
            output.sources.append(result)

    return output
