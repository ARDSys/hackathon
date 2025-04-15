from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from loguru import logger

from hackathon.beehealthy.agents.hot_topic_reviewer import (
    create_hot_topic_reviewer_agent,
)

from .agents.critique_analyst import create_critique_analyst_agent
from .agents.ethic_and_bias_analyst import create_ethics_and_bias_analyst_agent
from .agents.feasibility_analyst import create_feasibility_analyst_agent
from .agents.hypothesis_generator import create_hypothesis_generator_agent
from .agents.hypothesis_refiner import create_hypothesis_refiner_agent
from .agents.impact_analyst import create_impact_analyst_agent
from .agents.literature import create_literature_agent
from .agents.methodology_nice_reviewer import create_nice_reviewer_agent
from .agents.methodology_provider import create_methodology_provider_agent
from .agents.methodology_review_summary import (
    create_methodology_review_summary_agent,
)
from .agents.methodology_rude_reviewer import create_methodology_rude_reviewer_agent
from .agents.novelty_analyst import create_novelty_analyst_agent
from .agents.novelty_loop import create_novelty_loop_agent
from .agents.ontologist import create_ontologist_agent
from .agents.summary import create_summary_agent
from .state import HypgenState


def improve_hypothesis(
    state: HypgenState,
) -> Literal["hypothesis_refiner", "summary_agent"]:
    if state["iteration"] > 2:
        logger.info("Iteration limit reached after {} iterations", state["iteration"])
        return "summary_agent"
    if "ACCEPT" in state["critique"]:
        logger.info("Hypothesis accepted after {} iterations", state["iteration"])
        return "summary_agent"
    else:
        logger.info("Hypothesis rejected after {} iterations", state["iteration"])
        return "hypothesis_refiner"


def methodology_testing(
    state: HypgenState,
) -> Literal["methodology_provider", "hypothesis_refiner"]:
    if state["iteration"] > 2:
        logger.info("Iteration limit reached after {} iterations", state["iteration"])
        return "methodology_provider"
    if "ACCEPT" in state["critique"]:
        logger.info("Hypothesis accepted after {} iterations", state["iteration"])
        return "methodology_provider"
    else:
        logger.info("Hypothesis rejected after {} iterations", state["iteration"])
        return "hypothesis_refiner"


def novelty_loop_testing(
    state: HypgenState,
) -> Literal["hypothesis_generator", "literature_agent"]:
    """Decide whether to continue with the hypothesis or send it back for refinement based on novelty assessment."""

    # Safety check - initialize if not present
    if "novelty_loop_iteration" not in state:
        state["novelty_loop_iteration"] = 1

    # Log the current state
    logger.info(f"Novelty loop iteration: {state['novelty_loop_iteration']}")

    # Check if we've reached the maximum iterations
    if state["novelty_loop_iteration"] >= 4:
        logger.info(
            "Novelty loop iteration limit reached, proceeding to literature agent"
        )
        return "literature_agent"

    # Check if the hypothesis has been accepted as novel
    if state.get("novelty_loop_decision") == "ACCEPT":
        logger.info("Hypothesis accepted as novel, proceeding to literature agent")
        return "literature_agent"
    else:
        # If not novel enough, go back to hypothesis generator for refinement
        logger.info("Hypothesis needs more novelty, returning to hypothesis generator")
        return "hypothesis_generator"


def create_hypgen_graph() -> CompiledGraph:
    graph = StateGraph(HypgenState)

    # Hypothesis generation and assessment
    graph.add_node("ontologist", create_ontologist_agent("reasoning")["agent"])
    graph.add_node(
        "hypothesis_generator",
        create_hypothesis_generator_agent("reasoning")["agent"],
    )

    # Add the novelty loop agent to provide immediate feedback on hypothesis novelty
    graph.add_node("novelty_loop", create_novelty_loop_agent("reasoning")["agent"])

    graph.add_node("literature_agent", create_literature_agent("reasoning")["agent"])

    graph.add_node(
        "novelty_analyst", create_novelty_analyst_agent("reasoning")["agent"]
    )
    graph.add_node(
        "feasibility_analyst", create_feasibility_analyst_agent("reasoning")["agent"]
    )
    graph.add_node("impact_analyst", create_impact_analyst_agent("reasoning")["agent"])
    graph.add_node(
        "hot_topic_reviewer", create_hot_topic_reviewer_agent("reasoning")["agent"]
    )

    graph.add_node(
        "critique_analyst", create_critique_analyst_agent("reasoning")["agent"]
    )

    # Hypothesis feedback loop
    graph.add_node(
        "hypothesis_refiner", create_hypothesis_refiner_agent("reasoning")["agent"]
    )

    # Methodology testing loop
    graph.add_node(
        "methodology_provider",
        create_methodology_provider_agent("reasoning")["agent"],
    )
    graph.add_node("nice_reviewer", create_nice_reviewer_agent("reasoning")["agent"])
    graph.add_node(
        "bad_reviewer", create_methodology_rude_reviewer_agent("reasoning")["agent"]
    )
    graph.add_node(
        "methodology_reviewer",
        create_methodology_review_summary_agent("reasoning")["agent"],
    )

    # Summary
    graph.add_node("summary_agent", create_summary_agent("reasoning")["agent"])

    # Add edges
    graph.add_edge(START, "ontologist")
    graph.add_edge("ontologist", "hypothesis_generator")
    # From initial hypothesis
    graph.add_edge("hypothesis_generator", "novelty_loop")
    # From refined hypothesis
    graph.add_edge("hypothesis_refiner", "novelty_loop")

    # Add conditional edges from novelty_loop
    graph.add_conditional_edges(
        "novelty_loop",
        novelty_loop_testing,
        {
            "hypothesis_generator": "hypothesis_generator",
            "literature_agent": "literature_agent",
        },
    )

    # Fork for analysis
    graph.add_edge("literature_agent", "novelty_analyst")
    graph.add_edge("literature_agent", "feasibility_analyst")
    graph.add_edge("literature_agent", "impact_analyst")
    # graph.add_edge("literature_agent", "ethic_bias_analyst")
    graph.add_edge("literature_agent", "hot_topic_reviewer")

    # Join for critique
    graph.add_edge("novelty_analyst", "critique_analyst")
    graph.add_edge("feasibility_analyst", "critique_analyst")
    graph.add_edge("impact_analyst", "critique_analyst")
    # graph.add_edge("ethic_bias_analyst", "critique_analyst")
    graph.add_edge("hot_topic_reviewer", "critique_analyst")
    # Conditional edges for hypothesis improvement
    graph.add_conditional_edges(
        "critique_analyst",
        methodology_testing,
    )
    # graph.add_edge("critique_analyst", "methodology_provider")
    # Methodology testing loop
    graph.add_edge("methodology_provider", "nice_reviewer")
    graph.add_edge("methodology_provider", "bad_reviewer")
    graph.add_edge("nice_reviewer", "methodology_reviewer")
    graph.add_edge("bad_reviewer", "methodology_reviewer")

    graph.add_conditional_edges(
        "methodology_reviewer",
        improve_hypothesis,
    )
    # graph.add_edge("methodology_reviewer", "summary_agent")

    graph.add_edge("summary_agent", END)

    return graph.compile()


hypgen_graph = create_hypgen_graph()
