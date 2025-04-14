import logging
import os
from typing import Any, Dict, List
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph

logger = logging.getLogger("hypothesis_generator")
logging.basicConfig(level=logging.INFO)

class MultiAgentHypothesisGenerator(HypothesisGeneratorProtocol):
    """A multi-agent system for generating scientific hypotheses from subgraphs."""

    def __init__(self):
        """Initialize the hypothesis generator with required agents."""
        self.model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        self.temperature = float(os.environ.get("GEMINI_TEMPERATURE", 0.7))
        self.api_key = os.environ.get("GEMINI_KEY")

        if not self.api_key:
            raise ValueError("Missing GEMINI_KEY. Please set it in your environment variables.")

        # Используем Gemini (Google API)
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=self.temperature,
            google_api_key=self.api_key
        )

        self.gpt = ChatOpenAI(
            model = 'gpt-4',
            temperature = '0.9',
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
        )

        # Initialize conversation history for logging purposes
        self.conversation_history = []

    def run(self, subgraph: Subgraph) -> Hypothesis:
        """Generate a hypothesis from a subgraph using multiple collaborative agents.

        Args:
            subgraph: The source subgraph to analyze

        Returns:
            A fully formed Hypothesis object
        """
        logger.info(f"Starting hypothesis generation for subgraph: {subgraph.subgraph_id}")

        # Extract key information from subgraph
        context = subgraph.context or "No additional context provided."
        path = subgraph.to_cypher_string(full_graph=False)
        full_graph = subgraph.to_cypher_string(full_graph=True)

        # Step 1: Ontology Agent - Define concepts and relationships
        logger.info("Step 1: Ontology Agent analyzing concepts and relationships")
        ontology_analysis = self._run_ontology_agent(subgraph, path, context)
        self.conversation_history.append({"agent": "ontology", "content": ontology_analysis})

        # Step 2: Research Agent - Generate initial hypothesis
        logger.info("Step 2: Research Agent generating initial hypothesis")
        initial_hypothesis = self._run_research_agent(subgraph, path, ontology_analysis, context)
        self.conversation_history.append({"agent": "research", "content": initial_hypothesis})

        # Step 3: Critic Agent - Evaluate and provide feedback
        logger.info("Step 3: Critic Agent evaluating hypothesis")
        critique = self._run_critic_agent(initial_hypothesis, ontology_analysis, full_graph)
        self.conversation_history.append({"agent": "critic", "content": critique})

        # Step 4: Refinement Agent - Refine hypothesis based on critique
        logger.info("Step 4: Refinement Agent improving hypothesis")
        refined_hypothesis = self._run_refinement_agent(initial_hypothesis, critique, ontology_analysis, path)
        self.conversation_history.append({"agent": "refinement", "content": refined_hypothesis})

        # Step 5: Literature Agent - Find supporting references
        logger.info("Step 5: Literature Agent finding references")
        references = self._run_literature_agent(refined_hypothesis, subgraph)
        self.conversation_history.append({"agent": "literature", "content": str(references)})

        # Step 6: Final Synthesis Agent - Create the final hypothesis with all components
        logger.info("Step 6: Synthesis Agent creating final hypothesis")
        title, statement = self._run_synthesis_agent(refined_hypothesis, references, ontology_analysis)

        # Create and return the Hypothesis object
        return Hypothesis(
            title=title,
            statement=statement,
            source=subgraph,
            method=self,
            references=references,
            metadata={
                "conversation_history": self.conversation_history,
                "ontology_analysis": ontology_analysis,
                "initial_hypothesis": initial_hypothesis,
                "critique": critique,
                "refined_hypothesis": refined_hypothesis
            }
        )

    def _run_ontology_agent(self, subgraph: Subgraph, path: str, context: str) -> str:
        """Agent that analyzes and defines the key concepts in the subgraph."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an Ontology Agent specializing in scientific concept definition and relationship analysis.
            Your job is to carefully define each concept in the provided subgraph and explain the relationships between them.
            Analyze the provided knowledge graph path and identify the key scientific concepts and their relationships.
            """),
            HumanMessage(content=f"""
            Please analyze the following knowledge graph path and provide detailed definitions and relationship analyses:

            PATH:
            {path}

            ADDITIONAL CONTEXT:
            {context}
            """)
        ])

        response = self.llm(prompt.messages)
        return response.content

    def _run_research_agent(self, subgraph: Subgraph, path: str, ontology_analysis: str, context: str) -> str:
        """Agent that generates the initial hypothesis based on the subgraph."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a Research Agent with expertise in generating novel scientific hypotheses.
            Your task is to examine the knowledge graph path and ontological analysis, then formulate an initial scientific hypothesis.
            """),
            HumanMessage(content=f"""
            Based on the following knowledge graph path and ontological analysis, generate a novel scientific hypothesis:

            PATH:
            {path}

            ONTOLOGICAL ANALYSIS:
            {ontology_analysis}

            ADDITIONAL CONTEXT:
            {context}
            """)
        ])

        response = self.llm(prompt.messages)
        return response.content

    def _run_critic_agent(self, hypothesis: str, ontology_analysis: str, full_graph: str) -> str:
        """Agent that critically evaluates the hypothesis for scientific merit and gaps."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a Critic Agent with expertise in evaluating scientific hypotheses.
            Your task is to carefully analyze the proposed hypothesis and provide constructive criticism.
            """),
            HumanMessage(content=f"""
            Please critically evaluate the following scientific hypothesis:

            HYPOTHESIS:
            {hypothesis}

            ONTOLOGICAL ANALYSIS:
            {ontology_analysis}

            FULL KNOWLEDGE GRAPH:
            {full_graph}
            """)
        ])

        response = self.gpt(prompt.messages)
        return response.content

    def _run_refinement_agent(self, hypothesis: str, critique: str, ontology_analysis: str, path: str) -> str:
        """Agent that refines the hypothesis based on the critique."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a Refinement Agent specializing in improving scientific hypotheses.
            Your task is to refine an initial hypothesis based on critical feedback and ontological understanding.
            """),
            HumanMessage(content=f"""
            Please refine the following scientific hypothesis based on the critique and ontological analysis:

            INITIAL HYPOTHESIS:
            {hypothesis}

            CRITIQUE:
            {critique}

            ONTOLOGICAL ANALYSIS:
            {ontology_analysis}

            PATH:
            {path}
            """)
        ])

        response = self.llm(prompt.messages)
        return response.content

    def _run_literature_agent(self, refined_hypothesis: str, subgraph: Subgraph) -> List[str]:
        """Agent that generates relevant scientific references to support the hypothesis."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a Literature Agent with expertise in scientific publication knowledge.
            Your task is to generate plausible and relevant scientific references that would support the given hypothesis.
            """),
            HumanMessage(content=f"""
            Please generate relevant scientific references to support the following hypothesis:

            REFINED HYPOTHESIS:
            {refined_hypothesis}

            KEY CONCEPTS:
            {', '.join([subgraph.start_node, subgraph.end_node] + [node for node in subgraph.path_nodes if node not in [subgraph.start_node, subgraph.end_node]])}

            Generate 3-5 plausible references in standard academic citation format.
            """)
        ])

        response = self.llm(prompt.messages)
        references = [line.strip() for line in response.content.strip().split("\n") if line.strip()]
        return references

    def _run_synthesis_agent(self, refined_hypothesis: str, references: List[str], ontology_analysis: str) -> tuple[
        str, str]:
        """Agent that creates the final hypothesis with title and statement."""
        refs_text = "\n".join(references)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a Synthesis Agent specializing in creating clear, compelling scientific hypotheses.
            Your task is to create a final hypothesis with a concise title and detailed statement.
            """),
            HumanMessage(content=f"""
            Please create a final hypothesis with title and statement based on the following:

            REFINED HYPOTHESIS:
            {refined_hypothesis}

            SUPPORTING REFERENCES:
            {refs_text}

            ONTOLOGICAL ANALYSIS:
            {ontology_analysis}
            """)
        ])

        response = self.llm(prompt.messages)
        content = response.content

        title_match = content.split("TITLE:")[1].split("STATEMENT:")[0].strip() if "TITLE:" in content else ""
        statement_match = content.split("STATEMENT:")[1].strip() if "STATEMENT:" in content else content

        return title_match, statement_match

    def __str__(self) -> str:
        return "MultiAgentHypothesisGenerator"

    def to_json(self) -> dict[str, Any]:
        return {
            "name": str(self),
            "type": "multi_agent_system",
            "model": self.model_name,
            "temperature": self.temperature
        }