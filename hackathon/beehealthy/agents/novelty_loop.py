from typing import Any, Dict, List, Literal, Optional

from langchain.prompts import PromptTemplate
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..tools.perplexity import search_perplexity
from ..tools.pubmed import pubmed_tool

NOVELTY_LOOP_PROMPT = """
You are a critical scientific reviewer in a multi-agent research system. Your task is to critically evaluate the NOVELTY of a proposed hypothesis and provide a detailed assessment.

### Hypothesis to evaluate:
{hypothesis}

### Subgraph:
{subgraph}

### Context:
{context}

### Evaluation Process:
1. First, conduct additional targeted searches using the provided tools (PubMed, Perplexity) to ensure comprehensive literature coverage.
2. Focus your searches on identifying any existing research that directly addresses this hypothesis or its key components.
3. Analyze how novel this hypothesis is compared to existing literature.
4. Identify any gaps or opportunities that make this hypothesis novel.

### Novelty Assessment Criteria:
- Does the hypothesis propose a genuinely new idea, approach, or connection?
- Are there existing studies that have already addressed this hypothesis directly?
- Does it address an important gap in current knowledge?
- Does it combine existing concepts in a new and meaningful way?
- Is there significant overlap with well-established research?

### Your Output Must Include:

**1. Additional Search Queries Used:**  
List the targeted searches you performed to assess novelty.

**2. Novelty Assessment:**  
Provide your detailed assessment of novelty as one of:
- "Not Novel" - The hypothesis has been extensively studied already
- "Somewhat Novel" - The hypothesis has partial overlap with existing research but contains some new elements
- "Novel" - The hypothesis addresses a genuine gap and offers a new approach
- "Highly Novel" - The hypothesis represents a breakthrough idea with minimal precedent

**3. Evidence and Reasoning:**  
Explain your assessment with specific references to literature that either supports or contradicts the novelty claim.

**4. References:**  
List all relevant references used in your assessment, following proper academic citation format.

**5. Decision:**  
Based on your assessment, provide one of the following decisions:
- "ACCEPT" - if the hypothesis has significant novelty (Novel or Highly Novel) and should proceed in the workflow
- "REVISE" - if the hypothesis lacks sufficient novelty and should be revised

Your goal is to ensure that only truly novel hypotheses are advanced. Be thorough and critical, but fair in your assessment.
"""

tools = [
    pubmed_tool,
    search_perplexity,
]


def create_novelty_loop_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a novelty loop agent that evaluates hypothesis novelty using literature searches."""

    llm = get_model(model, **kwargs)
    novelty_reviewer = create_react_agent(model=llm, tools=tools)

    def extract_references(content: str) -> List[str]:
        """Extract references from the reviewer's response."""
        references = []
        if "References:" in content:
            refs_section = content.split("References:")[1].strip()
            # Extract individual references - one per line or numbered items
            for line in refs_section.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("- ")):
                    references.append(line)
        return references

    def extract_decision(content: str) -> str:
        """Extract the ACCEPT/REVISE decision from the content."""
        if "ACCEPT" in content:
            return "ACCEPT"
        else:
            return "REVISE"

    def agent(state: HypgenState) -> HypgenState:
        logger.info("Starting novelty loop evaluation")

        # Initialize novelty_loop_iteration if it doesn't exist
        if "novelty_loop_iteration" not in state:
            state = {**state, "novelty_loop_iteration": 0}

        # Increment the novelty loop iteration counter
        novelty_loop_iteration = state.get("novelty_loop_iteration", 0) + 1

        # Get current hypothesis and literature
        messages = (
            PromptTemplate.from_template(NOVELTY_LOOP_PROMPT)
            .invoke(state)
            .to_messages()
        )

        logger.info("Evaluating hypothesis novelty with additional searches")
        assistant_response = novelty_reviewer.invoke({"messages": messages})
        logger.info("Novelty evaluation completed")

        # Get the novelty assessment from the response
        novelty_assessment = assistant_response["messages"][-1]
        content = novelty_assessment.content

        # Extract references from the assessment
        references = extract_references(content)

        # Extract the decision (ACCEPT or REVISE)
        decision = extract_decision(content)
        logger.info(f"Novelty decision: {decision}")

        # Update state with novelty assessment, references, and iteration count
        return {
            "messages": assistant_response["messages"],
            "novelty_loop_output": content,
            "novelty_loop_decision": decision,
            "references": references,
            "novelty_loop_iteration": novelty_loop_iteration,
        }

    return {"agent": agent}
