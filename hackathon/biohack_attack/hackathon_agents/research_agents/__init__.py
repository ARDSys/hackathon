import asyncio

from typing import Union

from agents import Agent, Runner

from biohack_attack.model_factory import ModelFactory, ModelType

from .biorxiv_agent import biorxiv_agent
from .europmc_agent import europe_pmc_agent
from .hetionet_agent import hetionet_agent
from .pubmed_agent import pubmed_agent
from .semantic_scholar_agent import semantic_scholar_agent

from .models import QueriesOutput, ResearchAgentOutput, KnowledgeGraph, UnstructuredSource, Query, DataSource

RESEARCH_AGENT_DISPATCHER_PROMPT = """
You are an expert Graph Expansion System designed to analyze subgraphs and strategically query external data sources to 
enhance the graph's coverage, depth, and utility. Your purpose is to identify missing connections, nodes, and 
relationships that would make the graph more complete and valuable. You should return list of queries with relevenat keywords and data sources to query.
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
            if query.data_source == DataSource.HETIONET:
                result: KnowledgeGraph = await Runner.run(hetionet_agent, query.keyword)
                return True, result
            elif query.data_source == DataSource.PUBMED:
                result: UnstructuredSource = await Runner.run(
                    pubmed_agent, query.keyword
                )
                return False, result
            elif query.data_source == DataSource.BIORXIV:
                result: UnstructuredSource = await Runner.run(
                    biorxiv_agent, query.keyword
                )
                return False, result
            elif query.data_source == DataSource.EUROPE_PMC:
                result: UnstructuredSource = await Runner.run(
                    europe_pmc_agent, query.keyword
                )
                return False, result
            elif query.data_source == DataSource.SEMANTIC_SCHOLAR:
                result: UnstructuredSource = await Runner.run(
                    semantic_scholar_agent, query.keyword
                )
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
