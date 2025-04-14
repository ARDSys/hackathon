"""Group chat configuration for Hypegen.

This module manages the group chat and manager for the Hypegen system.
"""

import autogen
import openlit

from .agents import (
    assistant,
    comparison_agent,
    critic_agent,
    design_principles_agent,
    hypothesis_agent,
    mechanism_agent,
    novelty_agent,
    ontologist,
    outcome_agent,
    planner,
    scientist,
    unexpected_properties_agent,
    user,
)
from .langfuse import init_langfuse
from .llm_config import get_llm_config
from .prompts import MANAGER_PROMPT


def create_group_chat():
    """Create and configure the group chat and manager.

    Returns:
        A tuple containing the GroupChat and GroupChatManager instances
    """
    # Initialize Langfuse
    tracer = init_langfuse()
    # # Initialize OpenLIT instrumentation. The disable_batch flag is set to true to process traces immediately.
    openlit.init(tracer=tracer, disable_batch=True)

    # Reset the agents before creating a new group chat
    planner.reset()
    assistant.reset()
    ontologist.reset()
    scientist.reset()
    critic_agent.reset()

    # Create the group chat with all agents
    groupchat = autogen.GroupChat(
        agents=[
            user,
            planner,
            assistant,
            ontologist,
            scientist,
            hypothesis_agent,
            outcome_agent,
            mechanism_agent,
            design_principles_agent,
            unexpected_properties_agent,
            comparison_agent,
            novelty_agent,
            critic_agent,
        ],
        messages=[],
        max_round=20,
        admin_name="user",
        send_introductions=True,
        allow_repeat_speaker=True,
        speaker_selection_method="auto",
        select_speaker_message_template=MANAGER_PROMPT,
        select_speaker_auto_llm_config=get_llm_config("reasoning"),
    )

    # Create the group chat manager
    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config=get_llm_config("reasoning"),
        system_message=MANAGER_PROMPT,
    )

    return groupchat, manager, user
