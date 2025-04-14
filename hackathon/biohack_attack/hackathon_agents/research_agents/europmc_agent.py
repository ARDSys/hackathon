from agents import Agent, ModelSettings
from biohack_attack.hackathon_agents.research_agents.models import UnstructuredSource
from biohack_attack.hackathon_agents.research_agents.tools.search_api_tools import (
    get_europe_pmc_papers_by_keyword,
)
from biohack_attack.model_factory import ModelFactory, ModelType

europe_pmc_agent = Agent(
    name="Europe PMC Agent",
    instructions="Given keyword, perform the search in the Europe MPC database.",
    model=ModelFactory.build_model(ModelType.OPENAI),
    tools=[get_europe_pmc_papers_by_keyword],
    output_type=UnstructuredSource,
    model_settings=ModelSettings(tool_choice="required"),
)
