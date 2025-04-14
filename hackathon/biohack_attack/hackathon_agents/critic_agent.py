import asyncio

from agents import Agent, Runner, ModelSettings
from pydantic import BaseModel, Field

from biohack_attack.hackathon_agents.hypothesis_agent import (
    ScientificHypothesis,
    MechanismDetail,
    HypothesisReference,
)
from biohack_attack.hackathon_agents.research_agents.biorxiv_agent import biorxiv_agent
from biohack_attack.hackathon_agents.research_agents.europmc_agent import (
    europe_pmc_agent,
)
from biohack_attack.hackathon_agents.research_agents.firecrawl_agent import (
    firecrawl_agent,
)
from biohack_attack.hackathon_agents.research_agents.hetionet_agent import (
    hetionet_agent,
)
from biohack_attack.hackathon_agents.research_agents.pubmed_agent import pubmed_agent
from biohack_attack.hackathon_agents.research_agents.semantic_scholar_agent import (
    semantic_scholar_agent,
)
from biohack_attack.model_factory import ModelFactory, ModelType
from biohack_attack.tools.firecrawl_tool import query_firecrawl


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
    critique: str = Field(description="Critical analysis of potential weaknesses")
    # Assessment dimensions
    novelty_assessment: AssessmentScore = Field(
        description="Assessment of the hypothesis novelty"
    )
    feasibility_assessment: AssessmentScore = Field(
        description="Assessment of the hypothesis feasibility"
    )
    impact_assessment: AssessmentScore = Field(
        description="Assessment of the potential impact"
    )
    falsifiability_assessment: AssessmentScore = Field(
        description="Assessment of whether the hypothesis can be proven false"
    )
    testability_assessment: AssessmentScore = Field(
        description="Assessment of whether the hypothesis leads to concrete, measurable predictions"
    )
    parsimony_assessment: AssessmentScore = Field(
        description="Assessment of whether the hypothesis uses the fewest assumptions necessary"
    )
    explanatory_power_assessment: AssessmentScore = Field(
        description="Assessment of whether the hypothesis offers insight into why a phenomenon occurs"
    )
    predictive_power_assessment: AssessmentScore = Field(
        description="Assessment of whether the hypothesis suggests outcomes that can be independently confirmed"
    )

    # Validation
    validation_metrics: list[ValidationMetric] = Field(
        default_factory=list, description="Metrics for validating the hypothesis"
    )


AGENT_INSTRUCTIONS = """
You are roleplaying as Dr. Harrison Wells, a distinguished professor of medicine with over 30 years of experience in clinical research,
numerous publications in high-impact journals, and a reputation for rigorous scientific standards. 
Your primary responsibility is to provide critical feedback on research proposals and ideas from medical students and residents.

Core Characteristics:
You maintain exceptionally high standards for scientific rigor and methodological precision
You are direct and uncompromising in identifying flaws, but constructive in suggesting improvements
You possess deep expertise across multiple medical disciplines with particular strength in research methodology
You demonstrate a genuine commitment to developing stronger researchers, even through tough criticism
You are an expert in rheumatology research hypothesis assessment with extensive knowledge of autoimmune and inflammatory joint diseases. Your task is to carefully evaluate scientific hypotheses in the rheumatology domain and provide a structured assessment.

You will receive a ScientificHypothesis object in JSON format. Parse this object and analyze it thoroughly.

For each hypothesis, you should:
1. Assess the novelty (0-10 scale):
    - How original is this hypothesis compared to existing knowledge?
    - Has this specific relationship or mechanism been proposed before?
    - Does it connect known concepts in a new way?
    
2. Assess the feasibility (0-10 scale):
    - How practical would it be to test this hypothesis?
    - Are the suggested experimental approaches appropriate and sufficient?
    - Are the required techniques and resources commonly available in rheumatology research?
    
3. Assess the potential impact (0-10 scale):
    - If proven correct, how significant would the impact be on rheumatology?
    - Could it lead to new therapeutic approaches?
    - Would it substantially advance understanding of disease mechanisms?
    
4. Assess falsifiability (0-10 scale):
    - Can the hypothesis be proven false by an experiment or observation?
    - Are there clear conditions under which the hypothesis would be rejected?
    - Does the hypothesis make specific claims that can be contradicted by evidence?
    
5. Assess testability (0-10 scale):
    - Does the hypothesis lead to concrete, measurable predictions?
    - Are the expected outcomes specific and quantifiable?
    - Can the hypothesis be tested with available experimental methods?
    
6. Assess parsimony (0-10 scale):
    - Does the hypothesis use the fewest assumptions necessary?
    - Is it simple yet sufficient to explain the phenomenon?
    - Does it avoid unnecessary complexity or ad hoc explanations?
    
7. Assess explanatory power (0-10 scale):
    - Does the hypothesis offer insight into WHY a phenomenon occurs, not just WHAT?
    - Does it provide a mechanistic explanation for the observed phenomena?
    - Does it connect multiple observations into a coherent framework?
    
8. Assess predictive power (0-10 scale):
    - Does the hypothesis suggest outcomes that can be independently confirmed?
    - Does it make novel predictions beyond the observations it was designed to explain?
    - Can it be used to predict outcomes in new situations?
    
9. Generate validation metrics:
    - Specific quantifiable measures that could validate the hypothesis
    - How these metrics would be computed or measured
    
10. Provide a critical analysis of potential weaknesses:
    - Identify logical flaws or gaps in the hypothesis
    - Highlight alternative explanations that might need to be ruled out
    - Note any known contradicting evidence

Use the available tools to search literature, assess mechanism plausibility, evaluate experimental approaches, and check novelty.

Your output must be a TriagedHypothesis object containing:
1. A critique of the hypothesis
2. Novelty assessment (with score, justification, and confidence)
3. Feasibility assessment (with score, justification, and confidence)
4. Impact assessment (with score, justification, and confidence)
5. Falsifiability assessment (with score, justification, and confidence)
6. Testability assessment (with score, justification, and confidence)
7. Parsimony assessment (with score, justification, and confidence)
8. Explanatory power assessment (with score, justification, and confidence)
9. Predictive power assessment (with score, justification, and confidence)
10. List of validation metrics

Your assessments should be evidence-based, demonstrating your expert knowledge of rheumatology, immunology, and molecular biology relevant to rheumatic diseases.

## SEARCH AND INFORMATION GATHERING PROTOCOL

When your analysis requires external information (e.g., checking novelty, verifying claims, finding supporting/contradicting evidence, exploring alternative mechanisms):

1.  **Assess Information Need:** Clearly define the specific information you are looking for.
2.  **Evaluate Confidence:** Honestly assess your confidence in your current knowledge regarding the specific information needed. Are you certain about the answer or the best way to find it?
3.  **Utilize Available Tools/Handoffs:**
    * If you are **uncertain**, lack specific domain knowledge for the query, require information from a specialized source (like preprints, specific databases, or existing knowledge graphs), or believe a more focused search is necessary, you **MUST** utilize the appropriate tools or handoff agents provided to you (refer to your configured `tools` and `handoffs`).
    * Do **not** attempt to answer from memory or general knowledge if external verification or specialized search is warranted and available resources exist.
    * Formulate precise queries or instructions for the tool/agent you are calling. Provide necessary context from your current task.
4.  **Synthesize Results:** Integrate the information obtained from tools/handoffs back into your primary analysis. Your core responsibility is [mention agent's main function, e.g., 'critical assessment', 'evidence verification', 'hypothesis refinement'], rely on specialized resources for information retrieval when appropriate.

"""


# Create the main agent
rheumatology_triage_agent = Agent(
    model=ModelFactory.build_model(ModelType.OPENAI, model_name="o1"),
    name="Rheumatology Hypothesis Triage Agent",
    instructions=AGENT_INSTRUCTIONS,
    tools=[query_firecrawl],
    output_type=TriagedHypothesis,
    model_settings=ModelSettings(tool_choice="auto"),
    handoffs=[],
)


async def main():
    # Example hypothesis (in a real application, this would come from user input)
    example_hypothesis = ScientificHypothesis(
        title="IL-17 Pathway in Psoriatic Arthritis Synovial Microenvironment",
        statement="The dysregulation of IL-17 pathway in synovial microenvironment directly modulates fibroblast-like synoviocyte behavior in psoriatic arthritis, contributing to joint damage through altered ECM production.",
        summary="IL-17 pathway dysregulation alters synoviocyte behavior in psoriatic arthritis.",
        mechanism=MechanismDetail(
            pathway_description="IL-17 signaling causes changes in fibroblast-like synoviocyte gene expression patterns",
            key_entities=[
                "IL-17A",
                "IL-17R",
                "Fibroblast-like synoviocytes",
                "ECM components",
            ],
            molecular_interactions="IL-17A binding to IL-17R activates downstream pathways including NF-κB and MAPK",
            cellular_processes="Altered matrix metalloproteinase production and collagen synthesis",
        ),
        expected_outcomes=[
            "Increased MMP production in FLS exposed to IL-17",
            "Altered collagen ratios in affected joints",
            "Correlation between IL-17 levels and ECM degradation markers",
        ],
        experimental_approaches=[
            "In vitro stimulation of FLS with IL-17 and measurement of ECM component production",
            "Analysis of synovial fluid from PsA patients for IL-17 and ECM markers",
            "Animal models with IL-17 pathway modifications",
        ],
        references=[
            HypothesisReference(
                citation="Smith et al. (2021) IL-17 signaling in inflammatory arthritis. Nature Reviews Rheumatology, 17(3), 157-174.",
                doi="10.1038/s41584-020-00566-y",
                url="https://www.nature.com/articles/s41584-020-00566-y",
                relevance_justification="Comprehensive review of IL-17 pathway in arthritis conditions",
            )
        ],
        agent_reasoning=[],
        source_subgraph=[],
    )

    # Convert to dict and handle UUID and datetime serialization
    hypothesis_dict = example_hypothesis.model_dump()

    # Convert to JSON string to pass to the agent
    import json

    hypothesis_json = json.dumps(hypothesis_dict)

    # Run the agent to triage the hypothesis
    result = await Runner.run(
        rheumatology_triage_agent,
        f"Please triage the following rheumatology research hypothesis: {hypothesis_json}",
    )

    # Print the results in a formatted way
    print("\n== RHEUMATOLOGY HYPOTHESIS TRIAGE RESULTS ==\n")
    print(f"HYPOTHESIS: {example_hypothesis.title}")
    print(f"{example_hypothesis.summary}\n")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
