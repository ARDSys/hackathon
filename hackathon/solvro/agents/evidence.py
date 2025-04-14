import json
from typing import Any, Dict, Literal, Optional, List
from langchain.prompts import PromptTemplate
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage
from loguru import logger

from ..tools import arxiv_tool, pubmed_tool, bioportal_tool#, biorxiv_tool
from ..llm.utils import get_model
from ..state import EvidenceAgentPrivateState, HackathonState

EVIDENCE_PROMPT = """
You are a biomedical literature evidence agent.

Your task is to find supporting scientific literature for a biological relationship. Use literature tools and return your answer in valid JSON format ONLY. Do not include any extra explanation.

Return **1 to 3 references** only. Each reference must contain a title, source, and a brief snippet that supports the relationship.

JSON format:
{{
  "relation": "<source> -[:relation]-> <target>",
  "references": [
    {{
      "title": "Title of the paper",
      "authors": ["Last, F.", "Smith, A."],
      "year": 2021,
      "source": "PubMed",
      "url": "https://...",
      "snippet": "A short quote from the abstract or findings supporting the relation"
    }}
  ]
}}

Biological relation:
{source} -[:{relation}]-> {target}

Interpretation:
{interpretation}
"""

evidence_tools = ToolNode([
    pubmed_tool,
    arxiv_tool,
    # biorxiv_tool,
    bioportal_tool,
])

def create_evidence_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs
) -> Dict[str, Any]:
    llm = get_model(model, **kwargs)

    tool_agent = create_react_agent(
        model=llm,
        tools=evidence_tools,
        prompt=EVIDENCE_PROMPT,
        state_schema=EvidenceAgentPrivateState
    )

    def agent(state: EvidenceAgentPrivateState) -> HackathonState:
        summaries = state.get("mechanistic_summaries", []) or []
        updated_summaries = []

        for summary in summaries:
            updated_relationships = []

            for rel in summary.get("relationships", []):
                source = rel.get("source")
                target = rel.get("target")
                relation = rel.get("relation")
                interpretation = rel.get("interpretation", "")

                if not source or not target or not relation:
                    continue

                logger.info(f"📚 Searching evidence for: {source} -[:{relation}]-> {target}")
                prompt = PromptTemplate.from_template(EVIDENCE_PROMPT)
                messages = prompt.invoke({
                    "source": source,
                    "target": target,
                    "relation": relation,
                    "interpretation": interpretation
                }).to_messages()

                try:
                    response = tool_agent.invoke({
                        "messages": messages,
                        "mechanistic_summaries": summaries
                    })

                    raw = response["messages"][-1].content.strip()
                    # logger.debug(f"🧾 Raw model output for {source} -[:{relation}]-> {target}:\n{raw}")
                    parsed = json.loads(raw)

                    rel["references"] = parsed.get("references", [])

                except Exception as e:
                    logger.warning(f"⚠️ JSON parsing failed for relation {source} → {target}: {e}")
                    rel["references"] = []

                updated_relationships.append(rel)

            summary["relationships"] = updated_relationships
            updated_summaries.append(summary)

        return HackathonState(
            relationship_evidence_updates=updated_summaries,
            messages=state.get("messages", [])
        )

    return {"agent": agent}
