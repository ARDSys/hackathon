from agents import Agent, ModelSettings
from biohack_attack.hackathon_agents.research_agents.models import UnstructuredSource
from biohack_attack.hackathon_agents.research_agents.tools.search_api_tools import (
    get_biorxiv_papers_by_category,
)
from biohack_attack.model_factory import ModelFactory, ModelType

biorxiv_agent = Agent(
    name="Biorxiv Agent",
    instructions="Given keyword, perform the search in the Biorxiv database.",
    model=ModelFactory.build_model(ModelType.GEMINI),
    tools=[get_biorxiv_papers_by_category],
    output_type=UnstructuredSource,
    model_settings=ModelSettings(tool_choice="required"),
)
