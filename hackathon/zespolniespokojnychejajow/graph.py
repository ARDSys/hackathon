from typing import Literal
import os
import json
from pathlib import Path
import datetime

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from loguru import logger

from .agents.critique_analyst import create_critique_analyst_agent
from .agents.hypothesis_generator import create_hypothesis_generator_agent
from .agents.hypothesis_refiner import create_hypothesis_refiner_agent
from .agents.ontologist import create_ontologist_agent
from .agents.literature import create_literature_agent
from .agents.paper_agent import create_paper_agent
from .state import HypgenState


def save_ontologist_output(state: HypgenState) -> HypgenState:
    """Save the ontologist's output to a file for tracking purposes."""
    if "context" in state and state["context"]:
        # Create directory if it doesn't exist
        output_dir = Path("hackathon/zespolniespokojnychai/output/ontologist")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Generate a filename based on subgraph
        subgraph = state.get("subgraph", "")
        # Extract meaningful parts from subgraph for filename
        filename_base = "ontologist_analysis"
        if subgraph:
            # Try to extract node names from the subgraph
            import re
            nodes = re.findall(r'\(([^\)]+)\)', subgraph)
            if nodes and len(nodes) >= 2:
                filename_base = f"ontologist_{nodes[0]}_{nodes[-1]}"
        
        # Save as markdown
        md_file = output_dir / f"{filename_base}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"# Ontologist Analysis\n\n{state['context']}")
        
        # Save as JSON with more metadata
        json_file = output_dir / f"{filename_base}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({
                "context": state["context"],
                "subgraph": state.get("subgraph", ""),
                "timestamp": datetime.datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"Ontologist output saved to {md_file} and {json_file}")
    
    return state


def save_paper_output(state: HypgenState) -> HypgenState:
    """Save the paper agent's output to track processing of the comprehensive summary."""
    if "paper_summary" in state and state["paper_summary"]:
        logger.info(f"Paper agent generated a comprehensive research summary")
        
        # You can add more detailed logging here if needed
        if isinstance(state["paper_summary"], dict):
            if "title" in state["paper_summary"]:
                logger.info(f"Summary title: {state['paper_summary']['title']}")
            if "research_questions" in state["paper_summary"] and isinstance(state["paper_summary"]["research_questions"], list):
                logger.info(f"Generated {len(state['paper_summary']['research_questions'])} research questions")
        
        # Log information about embeddings
        if "paper_embeddings" in state and state["paper_embeddings"]:
            sections = list(state["paper_embeddings"].keys())
            logger.info(f"Generated embeddings for sections: {', '.join(sections)}")
    
    elif "papers_error" in state:
        logger.error(f"Paper agent encountered an error: {state['papers_error']}")
    
    return state


def save_literature_output(state: HypgenState) -> HypgenState:
    """Save the literature agent's output to track processing of papers."""
    if "literature" in state and state["literature"]:
        logger.info(f"Literature agent processed {len(state['literature'])} paper entries")
    elif "literature_error" in state:
        logger.error(f"Literature agent encountered an error: {state['literature_error']}")
    
    return state


def save_hypothesis_output(state: HypgenState) -> HypgenState:
    """Track intermediate hypothesis outputs - the final organization is handled by HypothesisGenerator."""
    if "hypothesis" in state and state["hypothesis"]:
        # Update the iteration count
        if "iteration" not in state:
            state["iteration"] = 0
        else:
            state["iteration"] += 1
        
        logger.info(f"Hypothesis version {state['iteration']} processed")
    
    return state


def improve_hypothesis(
    state: HypgenState,
) -> Literal["hypothesis_refiner", END]:
    if state["iteration"] > 2:
        logger.info("Iteration limit reached after {} iterations", state["iteration"])
        return END
    if "ACCEPT" in state["critique"]:
        logger.info("Hypothesis accepted after {} iterations", state["iteration"])
        return END
    else:
        logger.info("Hypothesis rejected after {} iterations", state["iteration"])
        return "hypothesis_refiner"


def create_hypgen_graph() -> CompiledGraph:
    graph = StateGraph(HypgenState)

    # Add nodes needed for hypothesis generation, critique, and refinement
    graph.add_node("ontologist", create_ontologist_agent("small")["agent"])
    graph.add_node("paper_agent", create_paper_agent("small")["agent"])
    graph.add_node(
        "hypothesis_generator", create_hypothesis_generator_agent("small")["agent"]
    )
    graph.add_node("critique_analyst", create_critique_analyst_agent("small")["agent"])
    graph.add_node(
        "hypothesis_refiner", create_hypothesis_refiner_agent("small")["agent"]
    )
    
    # Add nodes for saving outputs
    graph.add_node("save_ontologist_output", save_ontologist_output)
    graph.add_node("save_paper_output", save_paper_output)
    graph.add_node("save_hypothesis_initial", save_hypothesis_output)
    graph.add_node("save_hypothesis_refined", save_hypothesis_output)

    # Add edges for the workflow
    graph.add_edge(START, "ontologist")
    graph.add_edge("ontologist", "save_ontologist_output")
    graph.add_edge("save_ontologist_output", "paper_agent")
    graph.add_edge("paper_agent", "save_paper_output")
    graph.add_edge("save_paper_output", "hypothesis_generator")
    graph.add_edge("hypothesis_generator", "save_hypothesis_initial")
    graph.add_edge("save_hypothesis_initial", "critique_analyst")
    
    # Conditional edge for either accepting the hypothesis or refining it
    graph.add_conditional_edges(
        "critique_analyst",
        improve_hypothesis,
    )
    
    # After refinement, save the refined hypothesis and go back to critique
    graph.add_edge("hypothesis_refiner", "save_hypothesis_refined")
    graph.add_edge("save_hypothesis_refined", "critique_analyst")

    return graph.compile()

hypgen_graph = create_hypgen_graph()
