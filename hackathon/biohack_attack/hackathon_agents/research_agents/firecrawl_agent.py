from agents import Agent, ModelSettings
from biohack_attack.hackathon_agents.research_agents.models import UnstructuredSource
from biohack_attack.hackathon_agents.research_agents.tools.firecrawl import (
    query_firecrawl,
)
from biohack_attack.model_factory import ModelFactory, ModelType

firecrawl_agent = Agent(
    name="Pubmed Agent",
    instructions="Given keyword, perform the search in the Pubmed database using Firecrawl.",
    model=ModelFactory.build_model(ModelType.OPENAI),
    tools=[query_firecrawl],
    output_type=UnstructuredSource,
    model_settings=ModelSettings(tool_choice="required"),
)
