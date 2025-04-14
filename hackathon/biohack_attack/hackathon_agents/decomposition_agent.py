from typing import List, Optional

from agents import Agent, function_tool
from pydantic import BaseModel, Field

from biohack_attack.model_factory import ModelFactory, ModelType


class FalsifiableStatement(BaseModel):
    """A single fundamental statement that can be directly tested and falsified."""

    statement: str = Field(description="The precise statement in falsifiable form")
    falsification_method: str = Field(
        description="How this statement could be falsified/tested"
    )
    confidence_level: float = Field(
        description="Confidence that this is a fundamental component (0-1)"
    )
    supporting_evidence: Optional[str] = Field(
        None, description="Existing evidence supporting this statement"
    )
    contradicting_evidence: Optional[str] = Field(
        None, description="Existing evidence contradicting this statement"
    )


class HypothesisDecomposition(BaseModel):
    """Decomposition of a hypothesis into fundamental falsifiable statements."""

    original_hypothesis: str = Field(
        description="The original hypothesis being decomposed"
    )
    falsifiable_statements: List[FalsifiableStatement] = Field(
        description="List of fundamental falsifiable statements"
    )
    independence_assessment: str = Field(
        description="Assessment of whether the statements are truly independent"
    )
    completeness_assessment: str = Field(
        description="Assessment of whether the statements fully capture the original hypothesis"
    )


# Agent prompt with detailed instructions for hypothesis decomposition
AGENT_INSTRUCTIONS = """
You are an expert scientific hypothesis analyzer specializing in breaking down complex biomedical hypotheses into their most fundamental falsifiable statements. Your task is to decompose hypotheses into a set of clear, testable statements that can be independently verified or falsified.

## YOUR TASK

Analyze the input hypothesis and decompose it into 4-7 fundamental, falsifiable statements that:
1. Are specific enough to be directly tested in a laboratory or clinical setting
2. Cover the key claims and causal relationships in the original hypothesis
3. Could potentially be proven false with appropriate evidence
4. Are as independent from each other as possible

## DECOMPOSITION GUIDELINES

For each hypothesis:
1. Identify the core claims and causal relationships (A causes B, X influences Y)
2. Break down complex assertions into simpler components
3. Ensure each statement makes a single, testable claim
4. For each statement, describe a specific experimental or observational method to test it

## EXAMPLE

**Original Hypothesis:**
"The overexpression of IL-6 in synovial fluid drives the activation of fibroblast-like synoviocytes, leading to increased MMP production and subsequent cartilage degradation in rheumatoid arthritis."

**Example Falsifiable Statements:**
1. "IL-6 levels are elevated in the synovial fluid of RA patients compared to healthy controls."
   **Falsification Method:** "Measure IL-6 concentration in synovial fluid samples using ELISA."

2. "IL-6 directly activates fibroblast-like synoviocytes in vitro."
   **Falsification Method:** "Culture FLS with recombinant IL-6 and measure activation markers."

3. "Activated FLS produce increased levels of matrix metalloproteinases."
   **Falsification Method:** "Measure MMP production in activated vs. non-activated FLS."

4. "MMPs produced by activated FLS cause cartilage degradation."
   **Falsification Method:** "Co-culture activated FLS with cartilage explants and measure degradation products."

Remember that your goal is to provide statements that scientists could directly test. Make each statement specific and each falsification method practical and realistic.
"""

# Create the agent
hypothesis_decomposer_agent = Agent(
    model=ModelFactory.build_model(ModelType.OPENAI, model_name="o3-mini"),
    name="HypothesisDecomposerAgent",
    instructions=AGENT_INSTRUCTIONS,
    output_type=HypothesisDecomposition,
    tools=[],
)
