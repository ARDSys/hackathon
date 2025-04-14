from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from loguru import logger

from .agents.analysts import create_analyst_agent
from .agents.connector import create_connector_agent
from .agents.critique_analyst import create_critique_analyst_agent
from .agents.hypothesis_generator import create_hypothesis_generator_agent
from .agents.hypothesis_refiner import create_hypothesis_refiner_agent
from .agents.inspirations import create_inspiration_agent
from .agents.literature import create_literature_agent
from .agents.ontologist import create_ontologist_agent
from .agents.summary import create_summary_agent
from .agents.experiment_planner import create_experiment_planner_agent
from .agents.experiment_reviewer import create_experiment_reviewer_agent
from .agents.novelty_and_impact_reviewer import create_nai_agent

from .state import HypgenState


def improve_hypothesis(
    state: HypgenState,
) -> Literal["hypothesis_refiner", "summary_agent"]:
    if state["iteration"] > 3:
        logger.info("Iteration limit reached after {} iterations", state["iteration"])
        return "summary_agent"
    if "ACCEPT" in state["critique"]:
        logger.info("Hypothesis accepted after {} iterations", state["iteration"])
        return "summary_agent"
    else:
        logger.info("Hypothesis rejected after {} iterations", state["iteration"])
        return "hypothesis_refiner"


def create_seeding_graph() -> CompiledGraph:
    graph = StateGraph(HypgenState)

    # Add nodes with specialized agents
    graph.add_node("ontologist", create_ontologist_agent("small")["agent"])
    graph.add_node("connector", create_connector_agent("small")["agent"])
    graph.add_node("inspiration_agent", create_inspiration_agent("small")["agent"])
    graph.add_node("hypothesis_generator", create_hypothesis_generator_agent("small")["agent"])
    graph.add_node("experiment_planner", create_experiment_planner_agent("small")["agent"])
    graph.add_node("experiment_reviewer", create_experiment_reviewer_agent("small")["agent"])
    
    graph.add_node("hypothesis_refiner", create_hypothesis_refiner_agent("small")["agent"])
    
    graph.add_node("literature_agent", create_literature_agent("small")["agent"])
    graph.add_node("novelty_analyst", create_analyst_agent("novelty", "small")["agent"])
    graph.add_node(
        "feasibility_analyst", create_analyst_agent("feasibility", "small")["agent"]
    )
    graph.add_node("impact_analyst", create_analyst_agent("impact", "small")["agent"])
    graph.add_node("critique_analyst", create_critique_analyst_agent("small")["agent"])
    graph.add_node("summary_agent", create_summary_agent("small")["agent"])

    # Add edges
    graph.add_edge(START, "ontologist")
    graph.add_edge("ontologist","connector")
    graph.add_edge("connector", "inspiration_agent")
    graph.add_edge("inspiration_agent", "hypothesis_generator")
    graph.add_edge("hypothesis_generator", "literature_agent")
    graph.add_edge("hypothesis_refiner", "literature_agent")
    graph.add_edge("literature_agent", "novelty_analyst")
    graph.add_edge("literature_agent", "feasibility_analyst")
    graph.add_edge("literature_agent", "impact_analyst")
    # graph.add_edge("novelty_analyst", "critique_analyst")
    # graph.add_edge("feasibility_analyst", "critique_analyst")
    # graph.add_edge("impact_analyst", "critique_analyst")
    # graph.add_edge("critique_analyst", END)
    # graph.add_conditional_edges(
        # "critique_analyst",
        # improve_hypothesis,
    # )
    graph.add_edge("summary_agent", END)

    return graph.compile()


def create_refine_graph() -> CompiledGraph:
    graph = StateGraph(HypgenState)
    
    graph.add_node("experiment_planner", create_experiment_planner_agent("small")["agent"])
    graph.add_node("experiment_reviewer", create_experiment_reviewer_agent("small")["agent"])
    graph.add_node("hypothesis_refiner", create_hypothesis_refiner_agent("small")["agent"])    
    graph.add_node("literature_agent", create_literature_agent("small")["agent"])
    graph.add_node("novelty_and_impact_reviewer", create_analyst_agent("novelty", "small")["agent"])
    graph.add_node("feasibility_analyst", create_analyst_agent("feasibility", "small")["agent"])
    graph.add_node("impact_analyst", create_analyst_agent("impact", "small")["agent"])
    graph.add_node("critique_analyst", create_critique_analyst_agent("small")["agent"])
    graph.add_node("novel")
    # graph.add_node("summary_agent", create_summary_agent("small")["agent"])
    
    graph.add_edge(START, "experiment_planner")
    
    graph.add_edge("experiment_planner", "experiment_reviewer")
    graph.add_edge("experiment_reviewer", "hypothesis_refiner")
    graph.add_edge("hypothesis_refiner", "literature_agent")
    graph.add_edge("literature_agent", "novelty_analyst")
    graph.add_edge("literature_agent", "feasibility_analyst")
    graph.add_edge("literature_agent", "impact_analyst")
    graph.add_edge("")
    
    graph.add_edge("impact_analyst", END)
    
    graph.add_edge()    
    
    return graph.compile()

seeding_graph = create_seeding_graph()
refine_graph = create_refine_graph()