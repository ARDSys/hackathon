from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from loguru import logger

from .agents.final_judge import create_final_judge_agent
from .agents.hypotheses_generator import create_hypotheses_generator_agent
from .agents.hypotheses_judge import create_hypotheses_judge_agent
from .agents.hypothesis_refiner import create_hypothesis_refiner_agent
from .agents.literature import create_literature_agent
from .agents.knower import create_knower_agent
from .agents.dreamer import create_dreamer_agent
from .agents.review_summarizer import create_review_summarizer_agent
from .agents.reviewer import create_reviewer_agent
from .agents.reviewer_orchestrator import create_reviewer_orchestrator_agent
from .agents.summary import create_summary_agent
from .state import HypgenState
from ..consts import num_hypotheses


def improve_hypothesis(
        state: HypgenState,
) -> Literal["hypothesis_refiner", "summary_agent"]:
    if state["iteration"] > 2:
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

    # Add nodes with specialized agents
    graph.add_node("dreamer", create_dreamer_agent("small")["agent"])
    graph.add_node("knower", create_knower_agent("small")["agent"])
    graph.add_node("literature_agent", create_literature_agent("small")["agent"])
    graph.add_node("hypotheses_generator", create_hypotheses_generator_agent("small")["agent"])
    graph.add_node("hypotheses_judge", create_hypotheses_judge_agent("small")["agent"])

    for i in range(1,num_hypotheses+1):
        graph.add_node(f"reviewer_orchestrator_{i}", create_reviewer_orchestrator_agent(i, "small")["agent"])
        graph.add_node(f"reviewer_1_{i}", create_reviewer_agent(i, 1, "small")["agent"])
        graph.add_node(f"reviewer_2_{i}", create_reviewer_agent(i, 2,"small")["agent"])
        graph.add_node(f"reviewer_3_{i}", create_reviewer_agent(i, 3, "small")["agent"])
        graph.add_node(f"review_summarizer_{i}", create_review_summarizer_agent(i, "small")["agent"])
        graph.add_node(f"hypothesis_refiner_{i}", create_hypothesis_refiner_agent(i, "small")["agent"])



    graph.add_node("final_judge", create_final_judge_agent("small")["agent"])
    graph.add_node("summary_agent", create_summary_agent("small")["agent"])

    # Add edges
    graph.add_edge(START, "knower")
    # Finding paths to not generate hypotheses based on full graph
    # Literature review based on ontologies

    graph.add_edge("knower", "dreamer")
    graph.add_edge("dreamer", "literature_agent")

    # Form 10 initial hypothesis based on literature review

    graph.add_edge("literature_agent", "hypotheses_generator")

    # Judge the initial hypotheses and select top 3 based on literature review
    graph.add_edge("hypotheses_generator", "hypotheses_judge")

    # analyze each hypothesis separately
    for i in range(1, num_hypotheses+1):
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
