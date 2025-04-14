from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from loguru import logger

from .agents.analysts import create_analyst_agent
from .agents.critique_analyst import create_critique_analyst_agent
from .agents.hypothesis_generator import create_hypothesis_generator_agent
from .agents.hypothesis_refiner import create_hypothesis_refiner_agent
from .agents.literature import create_literature_agent
from .agents.ontologist import create_ontologist_agent
from .agents.summary import create_summary_agent
from .state import HypgenState


def improve_hypothesis(
        state: HypgenState,
) -> Literal["hypothesis_refiner", "summary_agent"]:
    if state["iteration"] > 3:
        logger.info("Iteration limit reached after {} iterations", state["iteration"])
        return "final_judge"
    if "ACCEPT" in state["critique"]:
        logger.info("Hypothesis accepted after {} iterations", state["iteration"])
        return "final_judge"
    else:
        logger.info("Hypothesis rejected after {} iterations", state["iteration"])
        return "hypothesis_refiner"


def create_hypgen_graph() -> CompiledGraph:
    graph = StateGraph(HypgenState)
    num_hypotheses = 3
    # Add nodes with specialized agents
    graph.add_node("ontologist", create_ontologist_agent("small")["agent"])
    graph.add_node(
        "hypotheses_generator", create_hypotheses_generator_agent("small")["agent"]
    )
    graph.add_node(
        "hypotheses_judge", create_hypotheses_judge_agent("small")["agent"]
    )
    graph.add_node(
        "hypotheses_judge", create_hypotheses_judge_agent("small")["agent"]
    )
    graph.add_node("literature_agent", create_literature_agent("small")["agent"])

    for i in range(num_hypotheses):
        graph.add_node(f"reviewer_orchestrator_{i}")
        graph.add_node(f"reviewer_1_{i}")
        graph.add_node(f"reviewer_2_{i}")
        graph.add_node(f"reviewer_3_{i}")
        graph.add_node(f"review_summarizer_{i}")
        graph.add_node(f"hypothesis_refiner_{i}")



    graph.add_node("final_judge", create_final_judge("small")["agent"])
    graph.add_node("summary_agent", create_summary_agent("small")["agent"])

    # Add edges
    graph.add_edge(START, "ontologist")
    # Finding paths to not generate hypotheses based on full graph
    # Literature review based on ontologies

    graph.add_edge("ontologist", "literature_agent")

    # Form 10 initial hypothesis based on literature review

    graph.add_edge("literature_agent", "hypotheses_generator")

    # Judge the initial hypotheses and select top 3 based on literature review
    graph.add_edge("hypotheses_generator", "hypotheses_judge")

    # analyze each hypothesis separately
    for i in range(num_hypotheses):
        graph.add_edge("hypotheses_judge", f"reviewer_orchestrator_{i}")
        # # Fork
        graph.add_edge(f"reviewer_orchestrator_{i}", f"reviewer_1_{i}")
        graph.add_edge(f"reviewer_orchestrator_{i}", f"reviewer_2_{i}")
        graph.add_edge(f"reviewer_orchestrator_{i}", f"reviewer_3_{i}")

        graph.add_edge(f"reviewer_1_{i}", f"review_summarizer_{i}")
        graph.add_edge(f"reviewer_2_{i}", f"review_summarizer_{i}")
        graph.add_edge(f"reviewer_3_{i}", f"review_summarizer_{i}")

        graph.add_conditional_edges(f"review_summarizer_{i}", improve_hypothesis,
                                    {
                                        "final_judge": "final_judge",
                                        "hypothesis_refiner": f"hypothesis_refiner_{i}"
                                    }
                                    )

    graph.add_edge("final_judge", "summary_agent")
    graph.add_edge("summary_agent", END)

    return graph.compile()


hypgen_graph = create_hypgen_graph()
