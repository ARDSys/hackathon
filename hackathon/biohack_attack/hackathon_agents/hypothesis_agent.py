from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID

from pydantic import BaseModel, Field


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
    # Core hypothesis information
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the hypothesis")
    title: str = Field(description="Concise title for the hypothesis")
    statement: str = Field(description="Detailed hypothesis statement")
    summary: str = Field(description="Brief summary of the hypothesis (1-2 sentences)")

    # Source information
    source_subgraph: Dict[str, Any] = Field(description="Reference to the original subgraph")
    generated_timestamp: datetime = Field(default_factory=datetime.now, description="When the hypothesis was generated")

    # Scientific details
    mechanism: MechanismDetail = Field(description="Details about the proposed mechanism")
    expected_outcomes: List[str] = Field(description="Expected outcomes if hypothesis is correct")
    experimental_approaches: List[str] = Field(description="Suggested approaches to test the hypothesis")

    # Supporting evidence
    references: List[HypothesisReference] = Field(default_factory=list,
                                                  description="Scientific references supporting the hypothesis")

    # Metadata
    generation_method: str = Field(description="Method used to generate the hypothesis")
    agent_reasoning: Dict[str, str] = Field(description="Reasoning steps from the agent that generated the hypothesis")
    keywords: List[str] = Field(description="Key terms related to the hypothesis")

    # Process metadata
    iteration_count: int = Field(description="Number of refinement iterations")
    refinement_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of refinements made")

    class Config:
        schema_extra = {
            "example": {
                "title": "TNF-α Mediated Microbiome Dysregulation in Rheumatoid Arthritis",
                "statement": "Elevated TNF-α levels in rheumatoid arthritis patients induce intestinal barrier dysfunction, leading to microbiome dysregulation that exacerbates immune dysregulation through altered metabolite production.",
                "summary": "TNF-α disrupts gut barrier function, altering the microbiome and worsening RA via metabolic changes.",
                "mechanism": {
                    "pathway_description": "TNF-α increases intestinal permeability through tight junction disruption",
                    "key_entities": ["TNF-α", "intestinal epithelium", "microbiome", "short-chain fatty acids"]
                },
                "novelty_assessment": {
                    "score": 7.5,
                    "justification": "Limited previous research on direct TNF-α effects on microbiome in RA context",
                    "confidence": 0.8
                }
            }
        }
