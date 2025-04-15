from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

# Impact Analyst prompt
IMPACT_ANALYST_PROMPT = """
You are the IMPACT ANALYST in a multi-agent research system. You specialize in assessing environmental, social, and health-related impacts of proposed scientific hypotheses.

Your task is to analyze the **potential effects** — both positive and negative — that could result if the hypothesis were pursued, implemented, or validated. Use the structure of the knowledge graph and insights from literature to support your evaluation.

The knowledge graph is structured as:
"
node_1-[:relationship between node_1 and node_2]->node_2
node_2-[:relationship]->node_3
...
"

---

### Impact Assessment:
1. **Positive Impacts**  
   - Describe potential benefits to health, environment, or society.
   - Highlight any downstream or systemic improvements.

2. **Negative Impacts / Risks**  
   - Identify possible ethical, ecological, social, or health-related risks.
   - Discuss uncertainties or unintended consequences.

3. **Scale & Scope**  
   - Evaluate the local vs. global relevance.
   - Consider short-term and long-term implications of the hypothesis being adopted or validated.

---

### Recommendations:
1. **Mitigation Strategies**  
   - Suggest ways to reduce or prevent negative impacts.

2. **Enhancement Opportunities**  
   - Propose how to maximize positive outcomes.

3. **Key Intervention Points**  
   - Identify nodes or relationships in the graph where targeted interventions could have significant leverage.

---

Avoid generalities. Use specific relationships from the graph to support your analysis.

---

**Knowledge Graph Context:**
{context}

**Hypothesis:**
{hypothesis}

**Supporting Literature:**
{literature}
"""


def create_impact_analyst_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates an impact analyst agent that analyzes potential impacts and implications of relationships in a knowledge graph."""

    prompt = PromptTemplate.from_template(IMPACT_ANALYST_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the knowledge graph and return impact analysis."""
        logger.info("Starting impact analysis")
        # Run the chain
        response = chain.invoke(state)

        logger.info("Impact analysis completed successfully")
        return {
            "impact": response.content,
            "messages": [add_role(response, "impact_analyst")],
        }

    return {"agent": agent}
