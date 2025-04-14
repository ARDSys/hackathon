"""Agent definitions for the Hypegen system.

This module defines all the agents used in the Hypegen system.
"""

import autogen
from autogen import AssistantAgent

from .functions import (
    rate_novelty_feasibility,
    response_to_query_perplexity,
)
from .llm_config import get_llm_config
from .prompts import (
    ASSISTANT_PROMPT,
    COMPARISON_AGENT_PROMPT,
    CRITIC_AGENT_PROMPT,
    DESIGN_PRINCIPLES_AGENT_PROMPT,
    HYPOTHESIS_AGENT_PROMPT,
    MECHANISM_AGENT_PROMPT,
    NOVELTY_AGENT_PROMPT,
    NOVELTY_ASSISTANT_PROMPT,
    ONTOLOGIST_PROMPT,
    OUTCOME_AGENT_PROMPT,
    PLANNER_PROMPT,
    SCIENTIST_PROMPT,
    UNEXPECTED_PROPERTIES_AGENT_PROMPT,
    USER_PROMPT,
    WRITER_PROMPT,
)

# User proxy agent for human interaction
user = autogen.UserProxyAgent(
    name="user",
    is_termination_msg=lambda x: x.get("content", "")
    and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    system_message=USER_PROMPT,
    llm_config=False,
    code_execution_config=False,
)

# Planner agent for creating task plans
planner = AssistantAgent(
    name="planner",
    system_message=PLANNER_PROMPT,
    llm_config=get_llm_config("reasoning"),
    description="Who can suggest a step-by-step plan to solve the task by breaking down the task into simpler sub-tasks.",
)

# Assistant agent for executing tools and functions
assistant = AssistantAgent(
    name="assistant",
    system_message=ASSISTANT_PROMPT,
    llm_config=get_llm_config("small"),
    description="""An assistant who calls the tools and functions as needed and returns the results. Tools include "rate_novelty_feasibility" and "generate_path".""",
)

writer = AssistantAgent(
    name="writer",
    system_message=WRITER_PROMPT,
    llm_config=get_llm_config("small"),
    description="""A writer who writes the final research proposal once all the aspects are expanded and reviewed by the scientists.""",
)

# Ontologist agent for defining terms and relationships
ontologist = AssistantAgent(
    name="ontologist",
    system_message=ONTOLOGIST_PROMPT,
    llm_config=get_llm_config("large"),
    description="I can define each of the terms and discusses the relationships in the path.",
)

# Scientist agent for creating research proposals
scientist = AssistantAgent(
    name="scientist",
    system_message=SCIENTIST_PROMPT,
    llm_config=get_llm_config("large"),
    description="I can craft the research proposal with key aspects based on the definitions and relationships acquired by the ontologist. I am **ONLY** allowed to speak after `Ontologist`",
)

# Specialized agents for expanding different aspects of the research proposal
hypothesis_agent = AssistantAgent(
    name="hypothesis_agent",
    system_message=HYPOTHESIS_AGENT_PROMPT,
    llm_config=get_llm_config("large"),
    description="""I can expand the "hypothesis" aspect of the research proposal crafted by the "scientist".""",
)

outcome_agent = AssistantAgent(
    name="outcome_agent",
    system_message=OUTCOME_AGENT_PROMPT,
    llm_config=get_llm_config("large"),
    description="""I can expand the "outcome" aspect of the research proposal crafted by the "scientist".""",
)

mechanism_agent = AssistantAgent(
    name="mechanism_agent",
    system_message=MECHANISM_AGENT_PROMPT,
    llm_config=get_llm_config("large"),
    description='''I can expand the "mechanism" aspect of the research proposal crafted by the "scientist"''',
)

design_principles_agent = AssistantAgent(
    name="design_principles_agent",
    system_message=DESIGN_PRINCIPLES_AGENT_PROMPT,
    llm_config=get_llm_config("large"),
    description="""I can expand the "design_principle" aspect of the research proposal crafted by the "scientist".""",
)

unexpected_properties_agent = AssistantAgent(
    name="unexpected_properties_agent",
    system_message=UNEXPECTED_PROPERTIES_AGENT_PROMPT,
    llm_config=get_llm_config("large"),
    description="""I can expand the "unexpected_properties" aspect of the research proposal crafted by the "scientist.""",
)

comparison_agent = AssistantAgent(
    name="comparison_agent",
    system_message=COMPARISON_AGENT_PROMPT,
    llm_config=get_llm_config("large"),
    description="""I can expand the "comparison" aspect of the research proposal crafted by the "scientist".""",
)

novelty_agent = AssistantAgent(
    name="novelty_agent",
    system_message=NOVELTY_AGENT_PROMPT,
    llm_config=get_llm_config("large"),
    description="""I can expand the "novelty" aspect of the research proposal crafted by the "scientist".""",
)

# Critic agent for reviewing the full proposal
critic_agent = AssistantAgent(
    name="critic_agent",
    system_message=CRITIC_AGENT_PROMPT,
    llm_config=get_llm_config("large"),
    description="""I can summarizes, critique, and suggest improvements after all seven aspects of the proposal have been expanded by the agents.""",
)

# Novelty assessment agent
novelty_assistant = autogen.AssistantAgent(
    name="novelty_assistant",
    system_message=NOVELTY_ASSISTANT_PROMPT,
    llm_config=get_llm_config("large"),
)

# Admin for novelty assessment
novelty_admin = autogen.UserProxyAgent(
    name="novelty_admin",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "")
    and x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
    llm_config=False,
)

# Register functions with agents
novelty_admin.register_for_execution()(response_to_query_perplexity)
novelty_assistant.register_for_llm(
    description="""This function is designed to search for academic papers using the Perplexity API based on a specified query. 
The query should be constructed with relevant keywords separated by "+". """
)(response_to_query_perplexity)

user.register_for_execution()(rate_novelty_feasibility)
planner.register_for_llm()(rate_novelty_feasibility)
assistant.register_for_llm(
    description="""Use this function to rate the novelty and feasibility of a research idea against the literature. The function uses semantic shcolar to access the literature articles.  
The function will return the novelty and feasibility rate from 1 to 10 (lowest to highest). The input to the function is the hypothesis with its details."""
)(rate_novelty_feasibility)
