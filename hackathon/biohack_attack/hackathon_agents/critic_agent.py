from typing import Optional

from pydantic import BaseModel, Field

from biohack_attack.hackathon_agents.hypothesis_agent import ScientificHypothesis


class ValidationMetric(BaseModel):
    """Metrics for validating the hypothesis."""
    name: str = Field(description="Name of the metric")
    value: float = Field(description="Value of the metric")
    description: str = Field(description="Description of what the metric means")
    computation_method: str = Field(description="How the metric was computed")


class AssessmentScore(BaseModel):
    """Assessment score for a specific dimension."""
    score: float = Field(description="Numerical score (typically 0-10 or 0-5)")
    justification: str = Field(description="Reasoning behind the score")
    confidence: float = Field(description="Confidence in this assessment (0-1)")


class TriagedHypothesis(BaseModel):
    # Assessment dimensions
    novelty_assessment: AssessmentScore = Field(description="Assessment of the hypothesis novelty")
    feasibility_assessment: AssessmentScore = Field(description="Assessment of the hypothesis feasibility")
    impact_assessment: AssessmentScore = Field(description="Assessment of the potential impact")

    # Validation
    validation_metrics: list[ValidationMetric] = Field(default_factory=list,
                                                       description="Metrics for validating the hypothesis")
    critique: Optional[str] = Field(None, description="Critical analysis of potential weaknesses")
