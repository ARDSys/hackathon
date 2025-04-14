from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

# Ontologist prompt
CONNECTOR_PROMPT = """You are exceptioanlly good at connecting facts.
    
Given some input with definitions of some terms and relatations between some facts you must create new connections between some facts you can extract from file  
You may try to create additional links using chain rule, so A -> B and then B -> C then you may create additional link like A -> C. You should consider if such linking makes any sense. 
Make sure to incorporate EACH of the relations you get in input.

Input format is like:
{{
### Definitions:
A clear definition of each term in the knowledge graph.
### Relationships
A thorough discussion of all the relationships in the graph. 
}}

Graph:
{subgraph}

You must return data in EXACTLY same format, only with some relationships added. 
"""


def create_connector_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a connector agent that analyzes and tries to create new relatiosn between facts."""

    prompt = PromptTemplate.from_template(CONNECTOR_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the definitions and relationships given and return some additional links betwween facts."""
        logger.info("Starting connecting facts")
        # Run the chain
        response = chain.invoke(state)

        logger.info("Added some connections")
        return {
            "context": response.content,
            "messages": [add_role(response, "connector")],
        }

    return {"agent": agent}
