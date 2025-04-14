from agents import Agent, ModelSettings
from biohack_attack.hackathon_agents.research_agents.models import KnowledgeGraph
from biohack_attack.hackathon_agents.research_agents.tools.hetionet import (
    query_hetionet,
)
from biohack_attack.model_factory import ModelFactory, ModelType

hetionet_agent = Agent(
    name="Hetionet Agent",
    instructions="Given keyword, perform the search in the Hetionet database.",
    model=ModelFactory.build_model(ModelType.OPENAI),
    tools=[query_hetionet],
    output_type=KnowledgeGraph,
    model_settings=ModelSettings(tool_choice="required"),
)
