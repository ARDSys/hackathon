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
You are a research assistant in a multi-agent scientific research system. Your task is to retrieve relevant scientific literature that can support the evaluation of a proposed hypothesis — specifically in terms of **novelty**, **feasibility**, and **impact**.

### Your Strategy:
- Design multiple broad but distinct search queries inspired by different aspects of the hypothesis.
- Avoid overly narrow or repetitive queries.
- Consider related domains, mechanisms, diseases, populations, or technologies that may provide indirect but useful insights.

---

### Hypothesis:
{hypothesis}

---

### Your Output Should Include:

**1. Search Queries Used:**  
List all the distinct, thoughtfully crafted search queries you used.

**2. Literature Results:**  
For each query, list 3–5 of the most relevant articles, including:  
- Title  
- Authors  
- Journal or Source  
- Year  
- Short summary or relevance note  

Group the results by the query they came from.

---

Avoid duplication. Prioritize relevance, diversity, and clarity. Your goal is to help downstream agents judge how well-studied the hypothesis space is, what gaps exist, and what potential risks or breakthroughs it implies.
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
            PromptTemplate.from_template(SEARCH_PROMPT).invoke(state).to_messages()
        )
        logger.info("Searching for relevant literature")
        assistant_response = research_assistant.invoke({"messages": messages})
        logger.info("Literature search completed")

        # Get the literature information from the response
        literature = assistant_response["messages"][-1]

        return {
            "messages": assistant_response["messages"],
            "literature": literature,
        }

    return {"agent": agent}
