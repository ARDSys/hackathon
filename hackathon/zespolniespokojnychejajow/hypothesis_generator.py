import re
import os
from typing import Any
from pathlib import Path
import json
import shutil

from langchain_core.runnables import RunnableConfig
from langfuse.callback import CallbackHandler

from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph

from .graph import hypgen_graph
from .state import HypgenState
from .utils import message_to_dict

langfuse_callback = CallbackHandler()


class HypothesisGenerator(HypothesisGeneratorProtocol):
    def run(self, subgraph: Subgraph) -> Hypothesis:
        context = subgraph.context
        path = subgraph.to_cypher_string(full_graph=False)

        res: HypgenState = hypgen_graph.invoke(
            {"subgraph": path, "context": context},
            config=RunnableConfig(callbacks=[langfuse_callback], recursion_limit=100),
        )

        title = self.__parse_title(res, subgraph) or ""
        statement = self.__parse_statement(res)
        
        # Create and organize the output files
        output_dir = self.__organize_output_files(res, title, statement, subgraph)
        
        return Hypothesis(
            title=title,
            statement=statement,
            source=subgraph,
            method=self,
            metadata={
                "summary": res.get("summary", ""),
                "context": res.get("context", ""),
                "novelty": res.get("novelty", ""),
                "feasibility": res.get("feasibility", ""),
                "impact": res.get("impact", ""),
                "critique": res.get("critique", ""),
                "iteration": res.get("iteration", 0),
                "messages": [message_to_dict(message) for message in res["messages"]],
                "output_dir": str(output_dir),
            },
        )

    def __parse_title(self, state: HypgenState, subgraph: Subgraph) -> str:
        title = state.get("title", "")
        if title:
            return title
        start_node = subgraph.start_node
        end_node = subgraph.end_node
        return f"Hypothesis for {start_node} -> {end_node}"

    def __parse_statement(self, state: HypgenState) -> str:
        statement_match = re.search(
            r"Hypothesis Statement:(.+?)$", state["hypothesis"], re.DOTALL
        )
        if statement_match:
            return statement_match.group(1)
        return state["hypothesis"]
    
    def __organize_output_files(self, state: HypgenState, title: str, statement: str, subgraph: Subgraph) -> Path:
        """Organize output files into a structured directory based on hypothesis title."""
        # Clean the title to make it a valid folder name
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        
        # Create main output directory
        output_base = Path("hackathon/zespolniespokojnychai/output")
        title_dir = output_base / safe_title
        title_dir.mkdir(exist_ok=True, parents=True)
        
        # Create subdirectories
        hypothesis_dir = title_dir / "hypothesis"
        ontologist_dir = title_dir / "ontologist"
        versions_dir = title_dir / "versions"
        hypothesis_dir.mkdir(exist_ok=True)
        ontologist_dir.mkdir(exist_ok=True)
        versions_dir.mkdir(exist_ok=True)
        
        # Save hypothesis files
        iteration = state.get("iteration", 0)
        self.__save_hypothesis_files(
            hypothesis_dir, 
            title, 
            statement, 
            state.get("hypothesis", ""), 
            state.get("critique", ""),
            iteration,
            subgraph
        )
        
        # Save current version in versions directory
        if iteration > 0:
            version_dir = versions_dir / f"version_{iteration}"
            version_dir.mkdir(exist_ok=True)
            self.__save_hypothesis_files(
                version_dir,
                title,
                statement,
                state.get("hypothesis", ""),
                state.get("critique", ""),
                iteration,
                subgraph
            )
        
        # Save ontologist files if available
        if "context" in state and state["context"]:
            self.__save_ontologist_files(
                ontologist_dir,
                state["context"],
                subgraph.to_cypher_string(full_graph=False)
            )
        
        # Copy ontologist files from the global ontologist directory if they exist
        self.__copy_ontologist_files(title, subgraph, ontologist_dir)
        
        return title_dir
    
    def __save_hypothesis_files(self, directory: Path, title: str, statement: str, 
                               full_hypothesis: str, critique: str, iteration: int, 
                               subgraph: Subgraph) -> None:
        """Save hypothesis files to the specified directory."""
        # Create markdown file
        md_path = directory / "hypothesis.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(f"## Hypothesis Statement\n\n{statement}\n\n")
            f.write(f"## Full Hypothesis\n\n{full_hypothesis}\n\n")
            if critique:
                f.write(f"## Critique\n\n{critique}\n\n")
            f.write(f"## Iteration\n\n{iteration}\n\n")
            f.write(f"## Subgraph\n\n```cypher\n{subgraph.to_cypher_string(full_graph=False)}\n```\n")
        
        # Create JSON file
        json_path = directory / "hypothesis.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "title": title,
                "statement": statement,
                "full_hypothesis": full_hypothesis,
                "critique": critique,
                "iteration": iteration,
                "subgraph": subgraph.to_cypher_string(full_graph=False)
            }, f, indent=2)
    
    def __save_ontologist_files(self, directory: Path, context: str, subgraph: str) -> None:
        """Save ontologist analysis files to the specified directory."""
        # Create markdown file
        md_path = directory / "ontologist_analysis.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# Ontologist Analysis\n\n")
            f.write(context)
            f.write(f"\n\n## Subgraph\n\n```cypher\n{subgraph}\n```\n")
        
        # Create JSON file
        json_path = directory / "ontologist_analysis.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "context": context,
                "subgraph": subgraph
            }, f, indent=2)
    
    def __copy_ontologist_files(self, title: str, subgraph: Subgraph, target_dir: Path) -> None:
        """Copy relevant ontologist files from the global ontologist directory if they exist."""
        # Try to find matching ontologist files from the global ontologist directory
        ontologist_base = Path("hackathon/zespolniespokojnychai/output/ontologist")
        
        if not ontologist_base.exists():
            return
        
        start_node = subgraph.start_node
        end_node = subgraph.end_node
        
        # Check for files with matching node names
        potential_files = [
            f for f in ontologist_base.glob("*.md") 
            if start_node.lower() in f.stem.lower() and end_node.lower() in f.stem.lower()
        ]
        
        # Copy any matching files
        for file in potential_files:
            # Copy markdown file
            if file.exists():
                shutil.copy2(file, target_dir / file.name)
            
            # Copy corresponding JSON file if it exists
            json_file = file.with_suffix(".json")
            if json_file.exists():
                shutil.copy2(json_file, target_dir / json_file.name)

    def __str__(self) -> str:
        return "HypeGen Generator"

    def to_json(self) -> dict[str, Any]:
        return {"type": "HypothesisGenerator"}
