from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

# Ontologist prompt
DREAMER_PROMPT = """You are a sophisticated ontologist.

Given some key concepts extracted from a comprehensive knowledge graph, your task is to identify the most prominent and non-trivial paths within the graph that could represent promising research hypotheses or areas worth further investigation.

Prioritize paths that (1) connect less obvious or previously underexplored relationships and (2) include intermediate nodes that may act as latent mediators or reveal indirect mechanisms.

Consider graph-theoretic properties (e.g., centrality, betweenness, novelty of connections) and scientific relevance (e.g., plausibility, potential impact, novelty).

There may be multiple relationships between the same two nodes. The format of the knowledge graph is
"
node_1-[:relationship between node_1 and node_2]->node_2
node_1-[:relationship between node_1 and node_3]->node_3
node_2-[:relationship between node_2 and node_3]->node_4...
"

You will be provided with a list of well-established and commonly pursued research paths to explicitly avoid or contrast against.


Graph:
{subgraph}

Commonly pursued research paths
{mainstream_paths}


Here is an example structure for our response, in the following format

{{
### Definitions:
A clear definition of each term in the knowledge graph.
### Relationships
A thorough discussion of all the relationships in the graph. 
}}
"""


def create_dreamer_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates an ontologist agent that analyzes and defines concepts from a knowledge graph."""

    prompt = PromptTemplate.from_template(DREAMER_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the knowledge graph and return definitions and relationships."""
        logger.info("Starting 'dreamer' ontology analysis")

        # Run the chain
        response = chain.invoke(state)

        logger.info("'Dreamer' ontology analysis completed successfully")
        return {
            "paths": response.content,
            "messages": [add_role(response, "dreamer")],
        }

    return {"agent": agent}
