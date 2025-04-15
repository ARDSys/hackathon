from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..tools.pubmed_by_year import search_pubmed_by_year
from ..utils import add_role

HOT_TOPIC_REVIEWER_PROMPT = """
You are a critical AI assistant collaborating with a group of scientists to assess the hot topic of a research proposal. 

Your primary task is to evaluate a proposed research hypothesis for its hot topic and current research trends.

To assess the hot topic status, you will:
1. Analyze the publication trends using PubMed by Year data
2. Evaluate the hypothesis against current research landscape
3. Identify key papers and their impact
4. Assess the novelty and potential impact of the proposed research

When searching PubMed, keep these guidelines in mind:
- Use concise search terms with relevant keywords rather than full sentences
- If a search returns insufficient results, try more general terms related to the core concepts
- Focus on one or two key concepts at a time instead of combining many terms
- For complex topics, breaking down searches into component parts may yield better results

Examples of query refinement:
- Instead of "Systemic Lupus Erythematosus Antinuclear Antibodies Interferon-alpha", try just "Lupus Interferon" or "Lupus Antibodies"
- Instead of "Cancer immunotherapy checkpoint inhibitors T-cell exhaustion", try "Cancer immunotherapy" or "checkpoint inhibitors"
- Instead of technical terms, sometimes using broader disease categories works better

Provide your reasoning for your assessment, including:
- Publication trends over the last 5 years
- Key papers and their impact
- Novelty of the proposed research
- Potential for future impact

Hypothesis:
{hypothesis}

Context:
{context}
"""

tools = [
    search_pubmed_by_year,
]


def create_hot_topic_reviewer_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a hot topic reviewer agent that evaluates the hot topic."""

    llm = get_model(model, **kwargs)
    research_assistant = create_react_agent(model=llm, tools=tools)

    def agent(state: HypgenState) -> HypgenState:
        logger.info("Starting hot topic reviewer")
        messages = (
            PromptTemplate.from_template(HOT_TOPIC_REVIEWER_PROMPT)
            .invoke(state)
            .to_messages()
        )
        logger.info("Searching for hot topic review")

        # First attempt with the agent
        assistant_response = research_assistant.invoke({"messages": messages})

        # Check if the response indicates insufficient search results
        last_message = assistant_response["messages"][-1].content
        if (
            "No sufficient data found for query" in last_message
            and "Please try a different search term" in last_message
        ):
            logger.info(
                "Initial search had insufficient results, trying with refined query"
            )

            # Add a guidance message to refine the search
            refine_message = {
                "role": "user",
                "content": "The search returned insufficient results. Please try again with more general keywords related to the core concepts, focusing on one or two key terms at a time.",
            }

            updated_messages = assistant_response["messages"] + [refine_message]
            assistant_response = research_assistant.invoke(
                {"messages": updated_messages}
            )

        logger.info("Hot topic review completed")

        # Get the literature information from the response
        hot_topic_review = assistant_response["messages"][-1]

        return {
            "messages": assistant_response["messages"],
            "hot_topic_review": add_role(hot_topic_review, "hot_topic_reviewer"),
        }

    return {"agent": agent}
