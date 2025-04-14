from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from loguru import logger

from .agents.graph_analyst import create_graph_analyst_agent
from .agents.context import create_context_agent
from .agents.evidence import create_evidence_agent
from .agents.hypothesis import create_hypothesis_synthesis_agent
from .agents.critic_analyst import create_critic_analyst_agent
from .state import HackathonState


def improve_hypothesis(
    state: HackathonState,
) -> Literal["graph_analyst", END]:
    if state["iteration"] > 3:
        logger.info("Iteration limit reached after {} iterations", state["iteration"])
        return END
    if "ACCEPT" in state["critique"]:
        logger.info("Hypothesis accepted after {} iterations", state["iteration"])
        return END
    else:
        logger.info("Hypothesis rejected after {} iterations", state["iteration"])
        logger.info("Critique feedback: {}", state["critique"])
        return "graph_analyst"

def create_hackathon_graph() -> CompiledGraph:
    graph = StateGraph(HackathonState)

    # Add nodes with specialized agents
    graph.add_node("graph_analyst", create_graph_analyst_agent("reasoning")["agent"])
    graph.add_node("context_agent", create_context_agent("small")["agent"])
    graph.add_node("evidence_agent", create_evidence_agent("small")["agent"])
    graph.add_node("hypothesis_generator", create_hypothesis_synthesis_agent("reasoning")["agent"])
    graph.add_node("critic_analyst", create_critic_analyst_agent("reasoning")["agent"])

    # Add edges
    graph.add_edge(START, "graph_analyst")
    
    # Fork
    graph.add_edge("graph_analyst", "context_agent")
    graph.add_edge("graph_analyst", "evidence_agent")
    
    # Join
    graph.add_edge("context_agent", "hypothesis_generator")
    graph.add_edge("evidence_agent", "hypothesis_generator")
    
    graph.add_edge("hypothesis_generator", "critic_analyst")
    
    graph.add_conditional_edges(
        "critic_analyst",
        improve_hypothesis,
    )

    return graph.compile()


hackathon_graph = create_hackathon_graph()
