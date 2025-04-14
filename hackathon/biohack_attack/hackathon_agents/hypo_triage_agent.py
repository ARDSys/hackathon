import asyncio
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

from agents import Agent, Runner, function_tool, WebSearchTool

from biohack_attack.hackathon_agents.hypothesis_agent import ScientificHypothesis, MechanismDetail, HypothesisReference
from biohack_attack.hackathon_agents.critic_agent import TriagedHypothesis
from biohack_attack.model_factory import ModelFactory, ModelType
# Agent tools
@function_tool
def search_literature(query: str) -> str:
    """
    Search for scientific literature related to the given query.
    
    Args:
        query: The search query related to the hypothesis.
        
    Returns:
        A summary of the search results.
    """
    # In a real implementation, this would interface with PubMed, Google Scholar, etc.
    if "IL-17" in query and "psoriatic arthritis" in query.lower():
        return """
        Found several relevant papers:
        1. Recent studies confirm IL-17's role in psoriatic arthritis pathogenesis
        2. IL-17 inhibitors show significant efficacy in treating psoriatic arthritis
        3. Research shows IL-17 directly affects fibroblast-like synoviocytes and matrix production
        4. Multiple studies connect IL-17 with ECM degradation in inflammatory joint diseases
        """
    elif "rheumatoid" in query.lower():
        return """
        Found several papers on rheumatoid arthritis mechanisms:
        1. TNF and IL-6 remain primary cytokines of interest
        2. JAK-STAT signaling pathways heavily implicated
        3. Fibroblast-like synoviocytes show altered behavior in RA
        """
    else:
        return f"Found several papers related to '{query}'. The research in this area appears active with increasing focus on molecular mechanisms."


# Create the main agent
rheumatology_triage_agent = Agent(
    # model=ModelFactory.build_model(ModelType.OPENAI),
    name="Rheumatology Hypothesis Triage Agent",
    instructions="""
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
       
    4. Generate validation metrics:
       - Specific quantifiable measures that could validate the hypothesis
       - How these metrics would be computed or measured
       
    5. Provide a critical analysis of potential weaknesses:
       - Identify logical flaws or gaps in the hypothesis
       - Highlight alternative explanations that might need to be ruled out
       - Note any known contradicting evidence
    
    Use the available tools to search literature, assess mechanism plausibility, evaluate experimental approaches, and check novelty.
    
    Your output must be a TriagedHypothesis object containing:
    1. A critique of the hypothesis
    2. Novelty assessment (with score, justification, and confidence)
    3. Feasibility assessment (with score, justification, and confidence)
    4. Impact assessment (with score, justification, and confidence)
    5. List of validation metrics
    
    
    Your assessments should be evidence-based, demonstrating your expert knowledge of rheumatology, immunology, and molecular biology relevant to rheumatic diseases.
    """,
    tools=[search_literature, WebSearchTool()],
    output_type=TriagedHypothesis,
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
        generation_method="Literature-based knowledge synthesis",
        keywords=["Psoriatic arthritis", "IL-17", "Fibroblast-like synoviocytes", "Extracellular matrix"],
        iteration_count=2,
        agent_reasoning=[],
    )
    
    # Convert to dict and handle UUID and datetime serialization
    hypothesis_dict = example_hypothesis.model_dump()
    
    # Convert to JSON string to pass to the agent
    import json
    hypothesis_json = json.dumps(hypothesis_dict)

    # Run the agent to triage the hypothesis
    result = await Runner.run(rheumatology_triage_agent, f"Please triage the following rheumatology research hypothesis: {hypothesis_json}")
    
    # Print the results in a formatted way
    print("\n== RHEUMATOLOGY HYPOTHESIS TRIAGE RESULTS ==\n")
    
    print(f"HYPOTHESIS: {example_hypothesis.title}")
    print(f"{example_hypothesis.summary}\n")
    
    print("ASSESSMENT SCORES:")
    print(f"- Novelty: {result.final_output.novelty_assessment.score}/10 (Confidence: {result.final_output.novelty_assessment.confidence})")
    print(f"  {result.final_output.novelty_assessment.justification}")
    
    print(f"\n- Feasibility: {result.final_output.feasibility_assessment.score}/10 (Confidence: {result.final_output.feasibility_assessment.confidence})")
    print(f"  {result.final_output.feasibility_assessment.justification}")
    
    print(f"\n- Impact: {result.final_output.impact_assessment.score}/10 (Confidence: {result.final_output.impact_assessment.confidence})")
    print(f"  {result.final_output.impact_assessment.justification}")
    
    print("\nVALIDATION METRICS:")
    for i, metric in enumerate(result.final_output.validation_metrics, 1):
        print(f"{i}. {metric.name} (Value: {metric.value})")
        print(f"   Description: {metric.description}")
        print(f"   Method: {metric.computation_method}")
    
    print("\nCRITIQUE:")
    print(result.final_output.critique)


if __name__ == "__main__":
    asyncio.run(main())