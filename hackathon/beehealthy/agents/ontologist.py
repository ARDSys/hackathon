from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

# Ontologist prompt
ONTOLOGIST_PROMPT = """You are a domain-specific ontologist operating within a multi-agent medical research system.

Given a structured subgraph from a comprehensive biomedical knowledge graph, your task is to:
1. Precisely define each node (concept) in the graph based on its contextual role in the graph, not using generic textbook definitions.
2. Analyze and explain the relationships between all nodes as represented by edges. There may be multiple, distinct relationships between the same nodes. All must be addressed.

Instructions:

- Use the structure below exactly:
  ### Definitions:
  - List and define each node (concept) that appears in the graph.
  - Definitions must reflect how the term is used in the specific context of the graph, based on the relationships it participates in.
  - Do not provide broad or general definitions that are disconnected from this graph.

  ### Relationships:
  - Describe each relationship (edge) in the graph.
  - Use the syntax of the graph structure to interpret directionality and meaning:
    node_a-[:relationship]->node_b
  - Be thorough. Include all relationships, even if multiple exist between the same pair of nodes.
  - Explain what each relationship means in the biomedical context, and how it reflects underlying biological, clinical, or methodological interactions.

Important notes:
- Do not add an introduction, summary, or conclusion.
- Use technical and precise language.
- Every concept and relationship in the graph must be included in your response.

Graph:
{subgraph}
"""


def create_ontologist_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates an ontologist agent that analyzes and defines concepts from a knowledge graph."""

    prompt = PromptTemplate.from_template(ONTOLOGIST_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the knowledge graph and return definitions and relationships."""
        logger.info("Starting ontology analysis")
        # Run the chain
        response = chain.invoke(state)

        logger.info("Ontology analysis completed successfully")
        return {
            "context": response.content,
            "messages": [add_role(response, "ontologist")],
        }

    return {"agent": agent}
