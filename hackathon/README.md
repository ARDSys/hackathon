# BeeARD Hackathon: Multi-Agent Scientific Hypothesis Generation

Welcome, innovators! We're excited to have you participate in this hackathon focused on advancing scientific discovery with AI.

## Inspiration

Our approach draws inspiration from several pioneering efforts in the field of autonomous scientific discovery. Sakana AI's _AI Scientist_ [1] envisions fully automated researchers, and recently achieved a major milestone with the first peer-reviewed publication authored by an AI scientist—demonstrating the viability of autonomous agents generating novel, publication-worthy ideas. SciAgents [2] explored the use of random path traversal through knowledge graphs to discover unexplored research directions. Their system transformed these traversals into subgraphs and used them as structured inputs for multi-agent systems, an idea we've embraced extensively in this hackathon to ground our hypothesis generation in meaningful graph-based context. Finally, Google's Co-Scientist project [3] highlights the power of extended deliberation via increased test-time compute, showing that giving AI systems more time to "think" can lead to hypotheses that are not only novel but experimentally validated. Together, these projects underscore the promise of combining structured knowledge, agent collaboration, and extended reasoning—a vision we aim to push forward with BeeARD.

## 🎯 The Goal

Your challenge is to **design and build a Multi-Agent System (MAS) that generates a novel research hypothesis based on a given subgraph.**

The core task involves creating a system that takes a `Subgraph` object as input and produces a `Hypothesis` object as output.

## 🧠 Understanding the Core Concepts

### 1. The Subgraph (`ard.subgraph.subgraph.Subgraph`)

Think of a vast Knowledge Graph (KG) containing interconnected scientific concepts, findings, and relationships extracted from literature. A `Subgraph` is a small, focused section of this larger KG, representing an interesting or potentially novel path between two or more concepts.

### **How are Subgraphs Created?**

Imagine an **"explorer" agent** journeying through a vast knowledge graph (KG), navigating connections between concepts like a scientist wandering through an interconnected landscape of ideas. As it traverses the KG, the path it follows forms what we call a **Subgraph**.

We've developed **custom traversal algorithms** that empower these agents to independently explore the graph, uncovering **unique and creative paths** through scientific domains. These subgraphs aren’t just random—they’re shaped by the agent's internal knowledge, learned patterns, and a touch of stochasticity.

**Why Subgraphs?**

Subgraphs serve as targeted prompts or creative seeds for your Multi-Agent System (MAS). Rather than navigating the entire knowledge graph (KG), your agents can zoom in on a focused cluster of concepts and relationships. Each subgraph distills a slice of the KG into a creative spark—activating the latent knowledge within Large Language Models and guiding agents toward novel scientific insights. In this system, subgraphs are not just data—they're catalysts for discovery.

**Key `Subgraph` Attributes:**

- `start_node`: The starting concept of the path.
- `end_node`: The ending concept of the path.
- `path_nodes`: The list of concepts forming the direct path.
- `get_path_edges()`: Returns the relationships (edges) along the direct path.
- `to_cypher_string()`: Provides a textual representation of the subgraph's nodes and relationships, useful for LLM prompts.
- `contextualize()`: (Optional) Can be used to generate an LLM-based analysis of the subgraph's content, providing richer context.
- It inherits from `KnowledgeGraph`, so you can use methods like `get_nodes()`, `get_edges()`, `get_node_attrs()`, etc.

_Feel free to explore the `src/ard/subgraph/subgraph.py` file for more details._

#### Example Subgraph

Here's a simplified example of what a Subgraph might look like:

```text
Subgraph(start="Inflammation", end="Alzheimer's Disease", path_length=3)

Path: Inflammation -> increases -> Amyloid Beta -> accumulates in -> Alzheimer's Disease

Additional nodes: Microglia, Tau Protein, Neuroinflammation
Additional relationships:
- Inflammation -> activates -> Microglia
- Microglia -> produces -> Neuroinflammation
- Neuroinflammation -> promotes -> Tau Protein
- Tau Protein -> contributes to -> Alzheimer's Disease
```

### 2. The Hypothesis (`ard.hypothesis.hypothesis.Hypothesis`)

This is the desired output of your MAS. A `Hypothesis` object encapsulates:

- `title`: A concise title for the hypothesis.
- `statement`: The core research hypothesis statement.
- `source`: A reference back to the `Subgraph` that inspired it.
- `method`: A reference to the `HypothesisGeneratorProtocol` implementation that created it.
- `references`: A list of scientific references supporting the hypothesis.
- `metadata`: A dictionary for any additional information (e.g., agent names, confidence scores, intermediate steps).

_See `src/ard/hypothesis/hypothesis.py` for the class definition._

#### Example Hypothesis

For the subgraph above, a generated hypothesis might look like:

```python
hypothesis = Hypothesis(
    title="Microglial-Mediated Neuroinflammation as a Link Between Systemic Inflammation and Alzheimer's Pathology",
    statement="Systemic inflammation activates microglia, leading to neuroinflammation that promotes both amyloid beta accumulation and tau pathology, accelerating Alzheimer's disease progression.",
    source=subgraph,  # The original subgraph object
    method=your_generator,  # Your generator implementation
    references=[
        "Smith et al. (2019). Neuroinflammation and Neurodegeneration. Journal of Neuroscience, 40(1), 123-145.",
        "Chen, J. & Wong, T. (2021). Microglial Activation in Alzheimer's Disease. Nature Reviews Neuroscience, 22(4), 210-228."
    ],
    metadata={
        "confidence": 0.85,
        "generated_by": "YourTeamName MAS",
        "agent_contributions": {
            "research_agent": "Identified the microglial activation pathway",
            "critic_agent": "Suggested including tau pathology connection"
        }
    }
)
```

## 🛠️ Your Task: Implement the `HypothesisGeneratorProtocol`

The only strict requirement for your solution is to **create a Python class that implements the `HypothesisGeneratorProtocol`**.

```python
# Located in: src/ard/hypothesis/types.py

from typing import Protocol, Any
from ard.subgraph import Subgraph
# Note: Type hint below uses string to avoid circular import
# from ard.hypothesis import Hypothesis

class HypothesisGeneratorProtocol(Protocol):
    def run(self, subgraph: Subgraph) -> "Hypothesis": ...

    def __str__(self) -> str: ... # For identifying your method

    def to_json(self) -> dict[str, Any]: ... # For serialization
```

Your `run` method will receive a `Subgraph` object and must return a fully formed `Hypothesis` object.

### Minimal Working Example

Here's a minimal example of implementing the protocol:

```python
from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class SimpleHypothesisGenerator(HypothesisGeneratorProtocol):
    """A simple hypothesis generator using a single LLM call."""

    llm: Any  # Your LLM client

    def run(self, subgraph: Subgraph) -> Hypothesis:
        # Convert subgraph to string representation for the LLM
        graph_text = subgraph.to_cypher_string()

        # Create a prompt for the LLM
        prompt = f"""
        Based on the following knowledge graph:

        {graph_text}

        Generate a scientific hypothesis that explains the relationship between
        {subgraph.start_node} and {subgraph.end_node}.

        Provide your response in this format:
        TITLE: [concise title for the hypothesis]
        HYPOTHESIS: [detailed hypothesis statement]
        REFERENCES: [list of references that support this hypothesis]
        """

        # Get response from LLM
        response = self.llm(prompt)

        # Parse response
        title_line = response.split("TITLE:")[1].split("HYPOTHESIS:")[0].strip()
        hypothesis_statement = response.split("HYPOTHESIS:")[1].split("REFERENCES:")[0].strip()

        # Parse references (if provided)
        references = []
        if "REFERENCES:" in response:
            references_text = response.split("REFERENCES:")[1].strip()
            # Simple parsing - split by newlines and filter empty lines
            references = [ref.strip() for ref in references_text.split("\n") if ref.strip()]

        # Create and return Hypothesis object
        return Hypothesis(
            title=title_line,
            statement=hypothesis_statement,
            source=subgraph,
            method=self,
            references=references,
            metadata={"generator": "SimpleHypothesisGenerator"}
        )

    def __str__(self) -> str:
        return "SimpleHypothesisGenerator"

    def to_json(self) -> Dict[str, Any]:
        return {
            "name": str(self),
            "type": "simple_llm_generator"
        }
```

## 🚀 Getting Started & Approaches

We encourage creativity! You can approach this challenge in several ways:

1.  **Modify Existing Workflows:**
    - Explore `hackathon/autogen/` and `hackathon/langgraph/`. These contain functional examples using popular MAS frameworks.
    - **Ideas:** Improve prompts, add new specialized agents (e.g., a Critic, a Literature Reviewer), integrate new tools for agents, refine the agent interaction logic.
2.  **Use the Sample Template:**
    - The `hackathon/sample/` directory provides a bare-bones structure. Use this as a clean slate to build your system using your preferred framework or approach.
3.  **Build From Scratch:**
    - Feel free to use any MAS framework (e.g., CrewAI, Camel-AI) or even build your agent orchestration logic from the ground up.

**Setup:**
Remember to set up your environment using UV:

```bash
# cd into the cloned ard repository
uv init
uv pip install -e .
# Make sure your API keys are set in a .env file (see .env.example)
```

## 📤 Submission Guidelines

To submit your solution:

1. **Fork the Repository**: Create your own fork of the ARD repository
2. **Implement Your Solution**: In the `hackathon/` directory, create a new folder with your team name
3. **Documentation**: Include a README.md in your folder explaining your approach
4. **Generate Evaluation Hypotheses**: One hour before the submission deadline, we will release 3 evaluation subgraphs. You must generate a hypothesis for each of these subgraphs using your solution.
5. **Submit a Pull Request**: Submit a PR back to the main repository including:
   - Your implementation code
   - Your README.md documentation
   - The 3 generated hypotheses (as JSON files)
   - **Detailed logs** of your system's execution for each hypothesis generation, showing agent interactions and decision processes
6. **Presentation**: Prepare a 5-minute presentation to showcase your solution

**Deadline**: 6:00 PM on April 14th

**Important**: Organizers will run your code as part of the evaluation process. Please ensure your solution:

1. Has clear instructions in your README.md on how to run your implementation
2. Includes a `.env.example` file with all required API keys (with dummy values)
3. Lists all dependencies beyond those in the core repository
4. Works without requiring manual intervention
5. **Includes logging capabilities** that capture agent interactions, ensuring transparency and verifiability of autonomous hypothesis generation
6. **Is fully reproducible** - technical judges will review your code and logs to verify that hypotheses were produced by your multi-agent system, not created manually

## ✨ Evaluation Criteria

The jury will prioritize these aspects when evaluating your submission:

- **Solution Quality & Innovation**: The technical implementation, code quality, and innovative approaches
- **Hypothesis Quality**: The scientific merit, relevance, and novelty of generated hypotheses
- **Methodological Approach**: The effectiveness and creativity of your multi-agent system design

**Important**:

- **Automated Generation**: Your submitted hypotheses should be generated by your system, not manually created. The 1-hour time constraint after receiving subgraphs is designed to emphasize automation.
- **System Runtime**: There is no time limit on how long your system takes to generate hypotheses, but your complete submission must be received within the 1-hour window after subgraphs are provided.
- **Testing**: Organizers will select one of your three hypotheses to verify it can be reproduced by running your code.

## 📚 Resources

- **Main Project README:** [README.md](README.md)
- **BeeARD Documentation:** [docs.beeard.ai](https://docs.beeard.ai/)
- **Core Classes:**
  - `Subgraph`: `src/ard/subgraph/subgraph.py`
  - `Hypothesis`: `src/ard/hypothesis/hypothesis.py`
  - `HypothesisGeneratorProtocol`: `src/ard/hypothesis/types.py`
- **Workflow Examples:** `hackathon/`

## 💡 Tips for Success

- **Leverage Subgraph Data:** Make sure your agents effectively use the nodes, edges, and potentially the `context` of the `Subgraph`. The `to_cypher_string()` method is helpful for prompts.
- **Agent Roles:** Think about different roles agents could play: generating ideas, criticizing, refining, searching for supporting evidence, ensuring clarity.
- **Prompt Engineering:** Craft clear and effective prompts for your LLM-powered agents.
- **Tools:** Consider giving agents tools (e.g., a function to search external databases, perform web searches, access to biomedical APIs etc).

---

## ❓ Frequently Asked Questions

### 🧠 LLMs & Technology

**Q: Do I need to use a specific LLM provider?**  
A: No, you can use any LLM provider (OpenAI, Anthropic, Cohere, etc.) as well as open-source models.

**Q: Can I use multiple different LLMs in my solution?**  
A: Yes, you can use different models for different agents or tasks.

**Q: Are there any restrictions on the technology we can use?**  
A: None at all. You're free to use any technology in the name of science.

**Q: Can we modify any part of the ARD codebase?**  
A: For this hackathon, please focus on implementing your solution within the existing framework rather than modifying the core code.

### 🛠️ Hackathon Logistics

**Q: Do I need to bring my own laptop?**  
A: Yes, please bring your own laptop.

**Q: Can I bring my own monitor?**  
A: Unfortunately, no. Due to limited space at the Google Office, personal monitors cannot be accommodated.

**Q: Will there be access to the internet?**  
A: Yes, high-speed internet will be available to all participants throughout the event.

**Q: What language will the hackathon be conducted in?**  
A: The event will be conducted in English.

**Q: Do I need to attend the event in person, or is online participation possible?**  
A: Attending in person is required.

**Q: What will be provided during the hackathon?**  
A: API keys for OpenAI, Firecrawl (for web access), Google Gemini, and food.

**Q: Can we submit multiple solutions?**  
A: No, please submit only one solution per team.

### 🔬 Scientific Domain

**Q: What scientific domain will we be working on?**  
A: While system design should be domain-agnostic, the focus during the hackathon will be on rheumatology.

## Good luck, and we can't wait to see the innovative hypothesis generation systems you create!

## References

- [1] [The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery](https://arxiv.org/abs/2408.06292)
- [2] [SciAgents: Automating scientific discovery through multi-agent intelligent graph reasoning](https://arxiv.org/abs/2409.05556)
- [3] [Towards an AI co-scientist](https://arxiv.org/abs/2502.18864)
