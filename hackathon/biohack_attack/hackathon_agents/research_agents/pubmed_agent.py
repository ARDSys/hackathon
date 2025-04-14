from agents import Agent, ModelSettings
from biohack_attack.hackathon_agents.research_agents.models import UnstructuredSource
from biohack_attack.hackathon_agents.research_agents.tools.search_api_tools import (
    get_pubmed_papers_by_keyword,
)
from biohack_attack.model_factory import ModelFactory, ModelType

pubmed_agent = Agent(
    name="Pubmed Agent",
    instructions="Given keyword, perform the search in the Pubmed database.",
    model=ModelFactory.build_model(ModelType.OPENAI),
    tools=[get_pubmed_papers_by_keyword],
    output_type=UnstructuredSource,
    model_settings=ModelSettings(tool_choice="required"),
)
