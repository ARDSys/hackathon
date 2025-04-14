import re
from typing import Any, Dict, List, Literal, Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from pydantic import BaseModel

from ..llm.utils import get_model
from ..state import HackathonState
from ..utils import add_role
from langchain_core.messages import AIMessage

class Relationship(BaseModel):
    source: str
    relation: str
    target: str
    interpretation: str


class KeyEntity(BaseModel):
    entity: str
    role: str


class MechanisticSummary(BaseModel):
    path_summary: str
    key_entities: List[KeyEntity]
    relationships: List[Relationship]


class GraphAnalysisOutput(BaseModel):
    mechanistic_summaries: List[MechanisticSummary]

# Graph Analyst prompt
GRAPH_ANALYST_PROMPT = """You are a biomedical graph analyst.

Given a subgraph extracted from a biomedical knowledge graph, your task is to identify and summarize each distinct mechanistic pathway or association described.

{critique_feedback}

The graph is formatted as:
"
node_1-[:relationship]->node_2
node_2-[:relationship]->node_3
...
"

Your task:
- Identify all biologically meaningful mechanistic paths or cascades in the graph.
- For each path identified, return:
  1. A short summary of the biological or pathological mechanism.
  2. A list of key entities and their roles (e.g., driver, mediator, endpoint).
  3. A list of relationships (edges), each with:
     - source node
     - target node
     - relationship type
     - biological interpretation

You MUST return the result in a structured JSON format matching the following structure:
{{
  "mechanistic_summaries": [
    {{
      "path_summary": "<mechanistic summary>",
      "key_entities": [
        {{"entity": "<entity name>", "role": "<role>"}}
      ],
      "relationships": [
        {{
          "source": "<node 1>",
          "relation": "<relation type>",
          "target": "<node 2>",
          "interpretation": "<biological meaning>" 
        }}
      ]
    }}
  ]
}}

Only include plausible paths from the graph. Do not invent relationships or concepts.

Graph:
{subgraph}
"""


def create_graph_analyst_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a Graph Analyst agent using OpenAI structured output."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a biomedical graph analyst."),
        ("human", GRAPH_ANALYST_PROMPT)
    ])

    llm = ChatOpenAI(name=model).with_structured_output(GraphAnalysisOutput)

    chain = prompt | llm

    def agent(state: HackathonState) -> HackathonState:
        logger.info("Starting structured graph analysis")

        subgraph_text = state["subgraph"]
        
        # Include critique feedback if available
        critique_feedback = ""
        if state.get("critique", "").startswith("REJECT"):
            critique_feedback = f"PREVIOUS CRITIQUE: {state.get('critique', '')}\nPlease consider this feedback when analyzing the graph for different mechanistic pathways."
        
        result: GraphAnalysisOutput = chain.invoke({
            "subgraph": subgraph_text,
            "critique_feedback": critique_feedback
        })

        logger.info(f"Subgraph analysis completed successfully, found {len(result.mechanistic_summaries)} pathways")
        return {
            "mechanistic_summaries": [summary.model_dump() for summary in result.mechanistic_summaries],
            "messages": [
                AIMessage(content="Graph analysis completed.", name="graph_analyst")
            ],
            # Preserve iteration counter
            "iteration": state.get("iteration", 0),
        }

    return {"agent": agent}
