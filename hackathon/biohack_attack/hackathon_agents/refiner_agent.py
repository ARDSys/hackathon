import asyncio
from pydantic import BaseModel, Field
from agents import Agent, Runner
from biohack_attack.hackathon_agents.hypothesis_agent import ScientificHypothesis, MechanismDetail, HypothesisReference
from biohack_attack.hackathon_agents.critic_agent import TriagedHypothesis, rheumatology_triage_agent
from biohack_attack.model_factory import ModelFactory, ModelType

ASSESSED_HYPOTHESIS_PROMPT = """
Please refine the following rheumatology research hypothesis based on the provided critique:
Hypothesis:
{hypothesis}

Critique:
{critique}
"""
    


AGENT_INSTRUCTIONS = """
You are roleplaying as Dr. Harrison Wells, a distinguished professor of medicine with over 30 years of experience in clinical research,
numerous publications in high-impact journals, and a reputation for rigorous scientific standards. 
Your primary responsibility is to refine research proposals from medical students and residents based on a provided feedback from domain experts.

Core Characteristics:
You maintain exceptionally high standards for scientific rigor and methodological precision
You are direct and uncompromising in identifying flaws, but constructive in suggesting improvements
You possess deep expertise across multiple medical disciplines with particular strength in research methodology
You demonstrate a genuine commitment to developing stronger researchers, even through tough criticism

Interaction Style:
When responding to research proposals, always:
Begin by identifying the core hypothesis or research question being presented.

Deliver constructive guidance:
Suggest specific, actionable improvements to address key weaknesses
Recommend relevant reading or alternative approaches
Acknowledge any genuinely promising elements (but only if truly present)

Improve provided hypothesis according to the critique by:

Address Critique Issues: Directly fix weaknesses identified in the critique.
Improve Low-Scoring Dimensions, especially:

If falsifiability is low: Add specific, testable predictions
If testability is low: Define concrete measurements
If feasibility is low: Simplify experimental approach or strengthen mechanism

Enhance Scientific Rigor:
Strengthen mechanism descriptions using key entities and interactions
Expand experimental approaches based on validation metrics
Link expected outcomes to specific testable predictions


Document Reasoning: List your refinements in the agent_reasoning field
Maintain Coherence: Ensure all components align with the central hypothesis
Remember that your ultimate goal is improving the quality of medical research, not simply criticizing.
Your feedback, while demanding, should always serve the purpose of developing more capable researchers and advancing medical science.
"""


# Create the main agent
rheumatology_refiner_agent = Agent(
    model=ModelFactory.build_model(ModelType.OPENAI),
    name="Rheumatology Hypothesis Refiner Agent",
    instructions=AGENT_INSTRUCTIONS,
    tools=[],
    output_type=ScientificHypothesis,
)


async def main():
    # Example hypothesis (in a real application, this would come from user input)
    example_hypothesis = ScientificHypothesis(
        title="IL-17 Pathway in Psoriatic Arthritis Synovial Microenvironment",
        statement="The dysregulation of IL-17 pathway in synovial microenvironment directly modulates fibroblast-like synoviocyte behavior in psoriatic arthritis, contributing to joint damage through altered ECM production.",
        summary="IL-17 pathway dysregulation alters synoviocyte behavior in psoriatic arthritis.",
        mechanism=MechanismDetail(
            pathway_description="IL-17 signaling causes changes in fibroblast-like synoviocyte gene expression patterns",
            key_entities=["IL-17A", "IL-17R", "Fibroblast-like synoviocytes", "ECM components"],
            molecular_interactions="IL-17A binding to IL-17R activates downstream pathways including NF-κB and MAPK",
            cellular_processes="Altered matrix metalloproteinase production and collagen synthesis"
        ),
        expected_outcomes=[
            "Increased MMP production in FLS exposed to IL-17",
            "Altered collagen ratios in affected joints",
            "Correlation between IL-17 levels and ECM degradation markers"
        ],
        experimental_approaches=[
            "In vitro stimulation of FLS with IL-17 and measurement of ECM component production",
            "Analysis of synovial fluid from PsA patients for IL-17 and ECM markers",
            "Animal models with IL-17 pathway modifications"
        ],
        references=[
            HypothesisReference(
                citation="Smith et al. (2021) IL-17 signaling in inflammatory arthritis. Nature Reviews Rheumatology, 17(3), 157-174.",
                doi="10.1038/s41584-020-00566-y",
                url="https://www.nature.com/articles/s41584-020-00566-y",
                relevance_justification="Comprehensive review of IL-17 pathway in arthritis conditions"
            )
        ],
        agent_reasoning=[],
        source_subgraph=[]
    )
    
    # Convert to dict and handle UUID and datetime serialization
    hypothesis_json = example_hypothesis.model_dump_json(indent=2)


    # Run the agent to triage the hypothesis
    result = await Runner.run(rheumatology_triage_agent, f"Please refine the following rheumatology research hypothesis: {hypothesis_json}")

    critique = result.final_output.model_dump_json(indent=2)

    refiner_prompt = ASSESSED_HYPOTHESIS_PROMPT.format(
        hypothesis=hypothesis_json,
        critique=critique
    )

    print(refiner_prompt)

    # Run the agent to refine the hypothesis
    result = await Runner.run(rheumatology_refiner_agent, refiner_prompt)
    
    # Print the results in a formatted way
    print("\n== RHEUMATOLOGY HYPOTHESIS REFINEMENT RESULTS ==\n")
    print(f"HYPOTHESIS: {example_hypothesis.title}")
    print(f"{example_hypothesis.summary}\n")
    print(result.final_output.model_dump_json(indent=2))



if __name__ == "__main__":
    asyncio.run(main())