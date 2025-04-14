from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

# Ontologist prompt
ONTOLOGIST_PROMPT = """You are a sophisticated ontologist.
    
Given some key concepts extracted from a comprehensive knowledge graph, your task is to define each one of the terms and discuss the relationships identified in the graph.

There may be multiple relationships between the same two nodes. The format of the knowledge graph is
"
node_1-[:relationship between node_1 and node_2]->node_2
node_1-[:relationship between node_1 and node_3]->node_3
node_2-[:relationship between node_2 and node_3]->node_4...
"

Make sure to incorporate EACH of the concepts in the knowledge graph in your response.

Do not add any introductory phrases. First, define each term in the knowledge graph and then, secondly, discuss each of the relationships, with context.

Here is an example structure for our response, in the following format

{{
### Definitions:
A clear definition of each term in the knowledge graph.
### Relationships
A thorough discussion of all the relationships in the graph. 
}}

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
