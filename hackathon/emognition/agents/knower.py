from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

# Ontologist prompt
KNOWER_PROMPT = """You are an analytical agent specializing in identifying well-established and commonly pursued research paths in a knowledge graph. Your goal is to surface the most obvious, canonical, and high-frequency connections in a given domain, and to assess whether these areas show signs of research saturation (i.e., diminishing returns from further study).

Given a knowledge graph enriched with metadata (e.g., number of supporting papers, citation counts, domain tags, and time trends), your tasks are to:

Identify and rank the most frequently studied or well-supported paths.

For each path:
Determine if it represents a mainstream or foundational research direction.
Evaluate whether the path is likely saturated, based on:
High publication volume with little recent novelty
Flattening citation trends
Repetition of study types or findings
Lack of emerging variables or hypotheses
Avoid novel, speculative, or rare connections—focus only on those with strong literature presence and broad recognition.

There may be multiple relationships between the same two nodes. The format of the knowledge graph is
"
node_1-[:relationship between node_1 and node_2]->node_2
node_1-[:relationship between node_1 and node_3]->node_3
node_2-[:relationship between node_2 and node_3]->node_4...
"

Graph:
{subgraph}

Output format:
path_1: node_1 -> [:relationship between node_1 and node_2] -> node_2 -> [:relationship between node_2 and node_3] -> node_3
path_2: node_1 -> [:relationship between node_1 and node_3] -> node_3 -> [:relationship between node_3 and node_4] -> node_4

"""


def create_knower_agent(
        model: Optional[Literal["large", "small", "reasoning"]] = None,
        **kwargs,
) -> Dict[str, Any]:
    """Creates an ontologist agent that analyzes and defines concepts from a knowledge graph."""

    prompt = PromptTemplate.from_template(KNOWER_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the knowledge graph and return definitions and relationships."""
        logger.info("Starting ontology analysis")
        # Run the chain
        response = chain.invoke(state)

        logger.info("Ontology analysis completed successfully")
        return {
            "mainstream_paths": response.content,
            "messages": [add_role(response, "knower")],
        }

    return {"agent": agent}
