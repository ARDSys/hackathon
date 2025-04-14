import asyncio

from agents import Runner, Agent, ModelSettings
from loguru import logger

from biohack_attack.hackathon_agents.decomposition_agent import (
    HypothesisDecomposition,
)
from biohack_attack.hackathon_agents.research_agents.firecrawl_agent import (
    firecrawl_agent,
)
from biohack_attack.hackathon_agents.verification_agent import (
    HypothesisVerification,
)
from biohack_attack.model_factory import ModelFactory, ModelType
from biohack_attack.tools.firecrawl_tool import query_firecrawl

# Define an agent to synthesize the individual statement verifications into a comprehensive hypothesis verification
ASSESSMENT_AGENT_INSTRUCTIONS = """
You are a scientific hypothesis assessment specialist tasked with synthesizing verification results for individual statements into a comprehensive assessment of an entire hypothesis.

## YOUR TASK

1. Analyze the verification results for each component statement of a hypothesis
2. Assess the cumulative strength of evidence for the overall hypothesis
3. Identify patterns of confirmation or disconfirmation across statements
4. Consider how weaknesses in individual components affect the overall hypothesis
5. Provide a detailed assessment and an aggregate verification score

## ASSESSMENT GUIDELINES

Consider these factors in your assessment:
1. The interdependence of the component statements
2. The relative importance of each component to the overall hypothesis
3. The quality and quantity of evidence for each component
4. The coherence of the evidence across components
5. The presence of any critical contradictions that undermine the hypothesis
6. The overall pattern of support vs. contradiction

Your output should be a comprehensive HypothesisVerification with:
1. The original hypothesis
2. All the individual statement verifications (included without modification)
3. A thorough overall assessment that synthesizes the verification results
4. An aggregate verification score representing the overall credibility of the hypothesis (0-1)

Remember that your goal is to provide an objective, evidence-based assessment of the hypothesis's overall validity based on the verification of its component statements.
"""

hypothesis_assessment_agent = Agent(
    model=ModelFactory.build_model(ModelType.OPENAI, model_name="o3-mini"),
    name="HypothesisAssessmentAgent",
    instructions=ASSESSMENT_AGENT_INSTRUCTIONS,
    output_type=HypothesisVerification,
    handoffs=[firecrawl_agent],
    model_settings=ModelSettings(
        tool_choice="required",
    ),
)
