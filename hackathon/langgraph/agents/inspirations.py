from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..tools.perplexity import search_perplexity
from ..tools.pubmed import pubmed_tool

SEARCH_PROMPT = """
You are a research assistant. Please find relevant literature that will help to create good hypothesis based on some definitions and relations you get on input.
To find a broad range of relevant literature, use queries that are related to the input but not too specific, also search for some already made expieriments on given matter.
Instead of one or two very specific queries, use a broader range of queries that are related to the hypothesis rethink literature you found and 
remove information you think is irrelevant to given definitiosn and relations.

{context}

After searching, return the search results.
"""

tools = [
    ArxivQueryRun(),
    pubmed_tool,
    search_perplexity,
]


def create_literatur_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a insipiartion literature agent for hypothesis generation."""

    llm = get_model(model, **kwargs)
    research_assistant = create_react_agent(model=llm, tools=tools)

    def agent(state: HypgenState) -> HypgenState:
        logger.info("Starting inspirational literature search")
        # Search for literature
        messages = (
            PromptTemplate.from_template(SEARCH_PROMPT)
            .invoke({"hypothesis": state["hypothesis"]})
            .to_messages()
        )
        logger.info("Searching for relevant inspirational literature")
        assistant_response = research_assistant.invoke({"messages": messages})
        logger.info("Inspirational literature search completed")

        # Get the literature information from the response
        literature = assistant_response["messages"][-1]

        return {
            "messages": assistant_response["messages"],
            "literature": literature,
        }

    return {"agent": agent}
