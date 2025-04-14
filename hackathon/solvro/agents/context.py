import json
from typing import Any, Dict, Literal, Optional, List

from langchain.prompts import PromptTemplate
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage
from loguru import logger

from ..tools.context import query_uniprot
from ..llm.utils import get_model
from ..state import ContextAgentPrivateState, HackathonState
from ..tools import arxiv_tool, pubmed_tool, bioportal_tool, biorxiv_tool

# Escaped JSON format to avoid variable parsing errors
CONTEXT_PROMPT = """
You are a biomedical entity enrichment assistant.

Your task is to enrich a given biomedical entity using ontology tools and return structured metadata. 
Return the result in **valid JSON format only**. Do not include any extra explanation or notes.

Limit the "definition" to **no more than 300 characters**.

Use the following format exactly:

{{
  "definition": "<Concise biological or clinical description, max 300 characters>",
  "ontology_id": "<Ontology or database identifier (e.g., UniProt accession)>",
  "synonyms": ["<synonym1>", "<synonym2>", ...]
}}

Entity to enrich:
{entity}
"""

context_tools = ToolNode([
    query_uniprot,
])

def create_context_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs
) -> Dict[str, Any]:
    llm = get_model(model, **kwargs)

    tool_agent = create_react_agent(
        model=llm,
        tools=context_tools,
        prompt=CONTEXT_PROMPT,
        state_schema=ContextAgentPrivateState
    )

    def agent(state: ContextAgentPrivateState) -> HackathonState:
        summaries = state.get("mechanistic_summaries", []) or []
        updated_summaries = []

        for summary in summaries:
            updated_entities = []

            for entry in summary.get("key_entities", []):
                entity = entry.get("entity")
                role = entry.get("role", "")

                if not entity:
                    continue

                logger.info(f"🔍 Enriching entity: {entity}")
                prompt = PromptTemplate.from_template(CONTEXT_PROMPT)
                messages = prompt.invoke({"entity": entity}).to_messages()

                try:
                    response = tool_agent.invoke({
                        "messages": messages,
                        "mechanistic_summaries": summaries
                    })

                    raw = response["messages"][-1].content.strip()
                    # logger.debug(f"🧾 Raw model output for '{entity}': {raw}")
                    parsed = json.loads(raw)

                except Exception as e:
                    logger.warning(f"❌ Failed to enrich {entity}: {e}")
                    parsed = {
                        "definition": raw if "raw" in locals() else "Unavailable",
                        "ontology_id": None,
                        "synonyms": []
                    }

                enriched = {
                    **entry,
                    "definition": parsed.get("definition", ""),
                    "ontology_id": parsed.get("ontology_id"),
                    "synonyms": parsed.get("synonyms", [])
                }

                updated_entities.append(enriched)

            summary["key_entities"] = updated_entities
            updated_summaries.append(summary)

        return HackathonState(
            entity_context_updates=updated_summaries,
            messages=state.get("messages", [])
        )

    return {"agent": agent}
