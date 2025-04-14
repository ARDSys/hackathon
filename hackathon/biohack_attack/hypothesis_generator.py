import asyncio
from typing import Any, List

from agents import Agent, Runner
from biohack_attack.hackathon_agents.research_agents.models import (
    QueriesOutput,
    ResearchAgentOutput,
)
from biohack_attack.model_factory import ModelFactory, ModelType
from dotenv import load_dotenv
from hackathon_agents.research_agents import perform_queries, research_agent_dispatcher
from loguru import logger
from pydantic import BaseModel

from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph


class HypothesisOutput(BaseModel):
    title: str
    statement: str
    reasoning_steps: list[str]


async def run_agents(subgraph: Subgraph) -> Hypothesis:
    # hypothesis_agent = Agent(
    #     name="Hypothesis create",
    #     instructions=f"Build novel scientific hypothesis based on the provided cypher path",
    #     model=ModelFactory.build_model(ModelType.OPENAI),
    #     output_type=HypothesisOutput
    # )
    # INPUT
    logger.info(f"Input graph: {subgraph}")
    path = subgraph.to_cypher_string(full_graph=True)

    # GENERATING QUERIES
    logger.info("Generating queries to external sources.")
    research_agent_results = await Runner.run(research_agent_dispatcher, path)
    queries: QueriesOutput = research_agent_results.final_output_as(QueriesOutput)
    logger.info(f"Reasoning: {queries.reasoning}")
    logger.info("List of queries:")
    for query in queries.queries:
        logger.info(f"Data Source: {query.data_source}, Keyword: {query.keyword}.")

    # PERFORMING QUERIES
    logger.info("Performing queries.")
    results: ResearchAgentOutput = await perform_queries(queries)
    logger.info(results)


    # Hypothesis generation Agent

    # result = await Runner.run(hypothesis_agent, path)
    # hypothesis_output: HypothesisOutput = result.final_output

    # return Hypothesis(
    #     title=hypothesis_output.title,
    #     statement=hypothesis_output.statement,
    #     source=subgraph,
    #     method=HypothesisGenerator(),
    # )


class HypothesisGenerator(HypothesisGeneratorProtocol):
    def run(self, subgraph: Subgraph) -> Hypothesis:
        return asyncio.run(run_agents(subgraph))

    def __str__(self) -> str:
        return "HypeGen Generator"

    def to_json(self) -> dict[str, Any]:
        return {"type": "HypothesisGenerator"}
