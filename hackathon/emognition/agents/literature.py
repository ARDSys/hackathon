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
You are a research assistant. Find and summarize relevant, high-quality knowledge from the literature that will help define and contextualize hypotheses related to the knowledge graph’s paths provided below.

To find a broad range of relevant literature, use queries that are related to the hypothesis but not too specific.
Instead of one or two very specific queries, use a broader range of queries that are related to the path.

Your tasks are to:
Search and retrieve the most relevant, peer-reviewed publications, preprints, or systematic reviews.
Summarize key findings that:
Directly support or challenge the relationship in question.
Provide mechanistic insight, historical context, or empirical results.
Include metadata like publication year, source, and study design (e.g., RCT, meta-analysis, observational).
Prioritize sources that are:
Recent (last 5–10 years unless foundational).
High-impact and well-cited.
Relevant to the domain and population of interest.
Provide a structured output for each finding:
Summary (2–4 sentences)
Source (title, authors, year, DOI or link)
Relevance (brief note on how it connects to the hypothesis or concept)

Paths:
{paths}

"""

tools = [
    ArxivQueryRun(),
    pubmed_tool,
    search_perplexity,
]


def create_literature_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a literature agent that finds relevant literature."""

    llm = get_model(model, **kwargs)
    research_assistant = create_react_agent(model=llm, tools=tools)

    def agent(state: HypgenState) -> HypgenState:
        logger.info("Starting literature search")
        # Search for literature
        messages = (
            PromptTemplate.from_template(SEARCH_PROMPT)
            .invoke({"context": state["context"]})
            .to_messages()
        )
        logger.info("Searching for relevant literature")
        assistant_response = research_assistant.invoke({"messages": messages})
        logger.info("Literature search completed")

        # Get the knowledge from the literature information from the response
        knowledge = assistant_response["messages"][-1]

        return {
            "messages": assistant_response["messages"],
            "knowledge": knowledge,
        }

    return {"agent": agent}
