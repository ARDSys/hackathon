from datetime import datetime
from typing import List, Optional

from agents import Agent
from pydantic import BaseModel, Field

from biohack_attack.model_factory import ModelFactory, ModelType


class HypothesisReference(BaseModel):
    """Scientific reference supporting the hypothesis."""
    citation: str = Field(description="Full citation in a standard format")
    doi: Optional[str] = Field(None, description="Digital Object Identifier if available")
    url: Optional[str] = Field(None, description="URL to the reference")
    relevance_justification: str = Field(description="Why this reference supports the hypothesis")


class MechanismDetail(BaseModel):
    """Details about the proposed mechanism in the hypothesis."""
    pathway_description: str = Field(description="Description of the biological pathway or mechanism")
    key_entities: List[str] = Field(description="Key biological entities involved in the mechanism")
    molecular_interactions: Optional[str] = Field(None, description="Details of molecular interactions if applicable")
    cellular_processes: Optional[str] = Field(None, description="Relevant cellular processes")


class ScientificHypothesis(BaseModel):
    """Represents a generated scientific hypothesis with review metrics."""
    agent_reasoning: list[str] = Field(description="Reasoning steps from the agent that generated the hypothesis")

    # Core hypothesis information
    title: str = Field(description="Concise title for the hypothesis")
    statement: str = Field(description="Detailed hypothesis statement")
    summary: str = Field(description="Brief summary of the hypothesis (1-2 sentences)")

    # Source information
    source_subgraph: list[str] = Field(description="Reference to the original subgraph")

    # Scientific details
    mechanism: MechanismDetail = Field(description="Details about the proposed mechanism")
    expected_outcomes: List[str] = Field(description="Expected outcomes if hypothesis is correct")
    experimental_approaches: List[str] = Field(description="Suggested approaches to test the hypothesis")

    # Supporting evidence
    references: List[HypothesisReference] = Field(default_factory=list,
                                                  description="Scientific references supporting the hypothesis")



hypothesis_agent = Agent(
    model=ModelFactory.build_model(ModelType.OPENAI),
    name="RheumatologyHypothesisGenerator",
    instructions="""You are an expert rheumatology researcher tasked with generating novel, scientifically sound hypotheses based on knowledge graph analysis. You will analyze subgraphs containing rheumatology-related concepts and relationships to identify meaningful connections and generate hypotheses.

## HYPOTHESIS EVALUATION CRITERIA
Your generated hypothesis must satisfy:
1. NOVELTY: Proposes connections not extensively studied in literature
2. BIOLOGICAL PLAUSIBILITY: Consistent with established mechanisms and pathways
3. SPECIFICITY: Defines a clear, detailed mechanism rather than vague associations
4. TESTABILITY: Can be evaluated through feasible experimental approaches
5. CLINICAL RELEVANCE: Has potential implications for diagnosis, treatment, or prevention
6. FALSIFIABILITY: Makes predictions that could prove the hypothesis incorrect

## INPUT PROCESSING INSTRUCTIONS
You will receive an OntologyAgentInput containing:
1. A subgraph with nodes and relationships to analyze
2. Potentially additional knowledge graphs and unstructured sources

For processing this input:
- Thoroughly examine all nodes and relationships in the provided subgraph
- Work with whatever mechanisms, entities, and relationships are present in the input
- Identify the most biologically meaningful paths between key concepts
- Focus on unexpected or underexplored connections that suggest knowledge gaps
- Consider both explicit connections and implicit relationships that could be inferred
- Pay special attention to nodes that bridge disparate biological processes
- Do not introduce mechanisms that are not supported by the input data

## OUTPUT STRUCTURE REQUIREMENTS
Generate a comprehensive ScientificHypothesis with:

1. title: Create a concise, specific title that clearly communicates the core hypothesis

2. statement: Formulate a precise hypothesis statement that specifies:
   - The key entities and their proposed relationship
   - The direction and nature of the effect
   - The specific mechanism of action based on the input data
   - Any relevant conditions or contexts

3. summary: Provide a 1-2 sentence distillation of the core hypothesis

4. mechanism: Detail the MechanismDetail with:
   - pathway_description: The complete biological pathway involved
   - key_entities: All critical molecules, cells, or processes from the input
   - molecular_interactions: Specific binding, signaling, or regulatory events
   - cellular_processes: Relevant cell behaviors or state changes

5. expected_outcomes: List specific, measurable outcomes if the hypothesis is correct

6. experimental_approaches: Propose 3-5 concrete methods to test the hypothesis

7. references: Provide relevant HypothesisReference objects that support aspects of your hypothesis

8. keywords: 5-10 specific terms relevant to your hypothesis

9. agent_reasoning: Document your step-by-step reasoning process, including:
   - Initial observations from the subgraph
   - Identification of key connections
   - Potential alternative explanations considered
   - Justification for the selected mechanism
   - Assessment against evaluation criteria

10. iteration_count and refinement_history: Set appropriately for your generation process

Your hypothesis should integrate the perspectives and information provided in the input while maintaining scientific precision and clarity. Focus on identifying the most biologically coherent pathways that suggest novel therapeutic targets, biomarkers, or disease mechanisms based strictly on the provided data.
""",
    output_type=ScientificHypothesis
)
