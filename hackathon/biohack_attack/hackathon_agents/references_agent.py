# /Users/zbigniewtomanek/PycharmProjects/hackathon/hackathon/biohack_attack/hackathon_agents/reference_generator_agent.py
# (Create a new file for this agent)

from typing import Optional

from agents import Agent
from pydantic import BaseModel, Field

from biohack_attack.model_factory import ModelFactory, ModelType


class Reference(BaseModel):
    """Scientific reference supporting the hypothesis."""

    citation: str = Field(description="Full citation in a standard format")
    doi: Optional[str] = Field(
        None, description="Digital Object Identifier if available"
    )
    url: Optional[str] = Field(None, description="URL to the reference")
    relevance_justification: str = Field(
        description="Why this reference supports the hypothesis"
    )

    def to_str(self) -> str:
        """Convert the reference to a string format."""
        return f"{self.citation} | DOI: {self.doi} | URL: {self.url} | Justification: {self.relevance_justification}"


class References(BaseModel):
    """Container for references related to a scientific hypothesis."""

    references: list[Reference] = Field(
        default_factory=list, description="List of references supporting the hypothesis"
    )


# Define Agent Instructions
REFERENCE_GENERATOR_INSTRUCTIONS = """
You are an Expert Hypothesis Referencer specializing in linking decomposed scientific statements to supporting evidence found within provided ontology enrichment data.

## YOUR TASK

Your goal is to enhance a given scientific hypothesis by adding relevant references based *only* on the information contained within the provided 'Ontology Enrichment Data'. You will receive:

1.  **Original Scientific Hypothesis:** The main hypothesis being worked on.
2.  **Decomposed Hypothesis:** The original hypothesis broken down into fundamental, falsifiable statements.
3.  **Ontology Enrichment Data:** A collection of unstructured text sources and knowledge graph triples gathered by previous research agents about the hypothesis context.

Based on these inputs, you must:

1.  **Analyze Falsifiable Statements:** Go through each `falsifiable_statements` in the `Decomposed Hypothesis`.
2.  **Search Provided Ontology Data:** For each statement, meticulously search *within* the `Ontology Enrichment Data` (`sources` and `graphs`) for snippets, facts, or relationships that directly support or relate to that specific statement. **DO NOT PERFORM NEW EXTERNAL SEARCHES.** Use *only* the data provided in the `Ontology Enrichment Data` section.
3.  **Identify Relevant Evidence:** Pinpoint specific pieces of information from the `Ontology Enrichment Data` that correspond to the claims made in the falsifiable statements.
4.  **Generate References:** For each relevant piece of evidence found, create a `HypothesisReference` object.
    * **citation:** Construct a descriptive citation. Indicate the source (e.g., "Finding from [Source ID]: [Brief snippet]" or "Relationship from [Graph ID]: [Subject Predicate Object]").
    * **doi/url:** Include if available in the *original* source data within the ontology output (this might often be missing, which is acceptable).
    * **relevance_justification:** Clearly explain *how* this specific piece of evidence from the ontology data supports the *particular falsifiable statement* it relates to.
5.  **Update Original Hypothesis:** Add all newly generated `HypothesisReference` objects to the `references` list of the **Original Scientific Hypothesis**. Make sure not to remove existing references.
6.  **Return Updated Hypothesis:** Output the *complete* `ScientificHypothesis` object, now including the newly added references.

## EXAMPLE REFERENCE GENERATION

**Falsifiable Statement:** "IL-6 levels are elevated in the synovial fluid of RA patients compared to healthy controls."

**Evidence found in Ontology Data (Source: 'pubmed_search_1'):** "A meta-analysis (PMID: 12345) confirmed significantly higher IL-6 concentrations in synovial fluid from RA patients versus controls (p < 0.001)."

**Generated HypothesisReference:**
```json
{
  "citation": "Finding from pubmed_search_1: Meta-analysis (PMID: 12345) confirmed significantly higher IL-6 concentrations in synovial fluid from RA patients vs controls (p < 0.001).",
  "doi": null,
  "url": "[https://pubmed.ncbi.nlm.nih.gov/12345](https://pubmed.ncbi.nlm.nih.gov/12345)", // If PMID lookup is possible *within the agent context* or if URL was stored. Often null.
  "relevance_justification": "This finding directly supports the statement that IL-6 levels are elevated in RA synovial fluid compared to controls, providing quantitative evidence (p < 0.001) from a meta-analysis."
}
"""
hypothesis_reference_generator_agent = Agent(
    model=ModelFactory.build_model(
        ModelType.OPENAI, model_name="o3-mini"
    ),  # Or another suitable model
    name="HypothesisReferenceGeneratorAgent",
    instructions=REFERENCE_GENERATOR_INSTRUCTIONS,
    output_type=References,  # The agent outputs the updated hypothesis
    tools=[],  # NO external search tools
    handoffs=[],  # NO handoffs for external search
    # Model settings can be default or adjusted if needed
    # model_settings=ModelSettings(...)
)
