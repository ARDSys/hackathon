from typing import List

from agents import Agent, ModelSettings
from pydantic import BaseModel, Field

from biohack_attack.hackathon_agents.research_agents.firecrawl_agent import (
    firecrawl_agent,
)
from biohack_attack.model_factory import ModelFactory, ModelType


class EvidenceItem(BaseModel):
    """Evidence found for or against a statement."""

    content: str = Field(description="The actual evidence text or summary")
    source: str = Field(description="Where this evidence was found")
    is_supporting: bool = Field(
        description="Whether this evidence supports or contradicts the statement"
    )
    confidence: float = Field(description="Confidence level in this evidence (0-1)")


class StatementVerification(BaseModel):
    """Verification result for a single falsifiable statement."""

    statement: str = Field(description="The statement being verified")
    falsification_method: str = Field(
        description="The method proposed to falsify the statement"
    )
    supporting_evidence: List[EvidenceItem] = Field(
        default_factory=list, description="Evidence supporting the statement"
    )
    contradicting_evidence: List[EvidenceItem] = Field(
        default_factory=list, description="Evidence contradicting the statement"
    )
    verification_conclusion: str = Field(
        description="Conclusion about the statement's validity based on evidence"
    )
    confidence_score: float = Field(
        description="Overall confidence in the verification result (0-1)"
    )


class HypothesisVerification(BaseModel):
    statement_verifications: List[StatementVerification] = Field(
        description="Verification results for each statement"
    )
    overall_assessment: str = Field(
        description="Overall assessment of the hypothesis quality"
    )
    verification_score: float = Field(
        description="Aggregate score for the verification (0-1)"
    )


VERIFICATION_AGENT_INSTRUCTIONS = """
You are an evidence verification specialist tasked with finding and analyzing scientific evidence to verify or falsify a specific scientific statement.

## YOUR TASK

1. Carefully analyze the given scientific statement to understand its claims, scope, and implications
2. Formulate strategic search queries to find relevant scientific literature using the available tools
3. Search for both supporting AND contradicting evidence for the statement
4. Analyze the collected evidence and draw a conclusion about the statement's validity
5. Provide a structured assessment including supporting evidence, contradicting evidence, and your overall conclusion

## SEARCH STRATEGY GUIDELINES

For effective verification:
1. Break down the statement into its core components for targeted searching
2. Use precise scientific terminology in your search queries
3. Search for both supportive and contradictory evidence
4. Prioritize recently published, peer-reviewed research
5. Consider the quality and reliability of different sources
6. Examine methodology and study limitations when assessing evidence

## EVIDENCE ASSESSMENT GUIDELINES

When analyzing the evidence:
1. Evaluate the methodological quality of studies (sample size, controls, etc.)
2. Consider the consistency of findings across multiple studies
3. Assess the relevance and directness of the evidence to the specific statement
4. Weigh contradictory evidence fairly
5. Consider the strength of the causal relationships implied
6. Note any limitations or gaps in the available evidence

Your output should be a comprehensive StatementVerification object with:
1. The original statement
2. The proposed falsification method
3. Supporting evidence items with sources
4. Contradicting evidence items with sources
5. A clear verification conclusion
6. An overall confidence score

Remember that your goal is to provide an objective, evidence-based assessment of the statement's validity based on current scientific knowledge.
"""

statement_verification_agent = Agent(
    model=ModelFactory.build_model(ModelType.OPENAI, model_name="o3-mini"),
    name="StatementVerificationAgent",
    instructions=VERIFICATION_AGENT_INSTRUCTIONS,
    handoffs=[firecrawl_agent],
    output_type=StatementVerification,
    model_settings=ModelSettings(tool_choice="required"),
)
