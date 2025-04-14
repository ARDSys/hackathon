# LangGraph Workflow

This workflow implements a hypothesis generation system using LangGraph, designed to analyze subgraphs and generate scientific hypotheses based on the relationships and context within the data.

## Overview

The workflow consists of several key components:

- `generate_hypothesis.py`: CLI interface for running the hypothesis generation
- `hypothesis_generator.py`: A wrapper around the hypothesis generation logic
- `graph.py`: Defining the LangGraph workflow structure - the logic
- `state.py`: Manages the state during hypothesis generation
- `utils.py`: Utility functions supporting the workflow
- `agents`: A collection of agents for the workflow
- `tools`: A collection of tools for the agents to use
- `llm`: A collection of LLM configurations

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) package and project manager

## Environment Setup

1. Create a `.env` file in the project root with the following variables:

   ```
   # OpenAI
    OPENAI_API_KEY=sk-proj-123

    # Anthropic
    ANTHROPIC_API_KEY=sk-ant-api03-123

    # Perplexity
    PPLX_API_KEY=pplx-123

    # PubMed
    PUBMED_API_KEY=123

    # Langfuse
    LANGFUSE_SECRET_KEY=sk-lf-123
    LANGFUSE_PUBLIC_KEY=pk-lf-123
    LANGFUSE_HOST=https://cloud.langfuse.com
   ```

## Installation

Install the packages in the ard's root directory:

```bash
uv sync
source .venv/bin/activate
```

## Usage

The workflow can be run using the `generate_hypothesis.py` script.
From ARD's root directory:

```bash
python -m hackathon.langgraph.generate_hypothesis -f data/Bridge_Therapy.json --output hackathon/langgraph/output
```

### Arguments

- `--file` or `-f`: Path to the input JSON file containing the subgraph data
- `--output` or `-o`: Path to the output directory (defaults to current directory)

## Output

The output is a JSON and Markdown files containing the hypothesis.

```json
{
    "title": "<hypothesis.title>",
    "text": "<hypothesis.statement>",
    "references": [],
    "hypothesis_id": "<hypothesis._hypothesis_id",
    "subgraph_id": "<source_subgraph_id",
    "source": "<source_subgraph_as_json>",
    "metadata": {
        ... # all additional data from the hypothesis
    }
}
```

## Architecture

The workflow uses LangGraph to create a structured process for hypothesis generation:

1. Takes a subgraph as input
2. Processes subgraph through `method` (e.g. `HypothesisGenerator`)
3. Creates Hypothesis from the state returend by the `method`
4. Saves the Hypothesis to the output directory

## Development

To modify or extend the workflow:

1. Edit `graph.py` to modify the workflow structure
2. Update `hypothesis_generator.py` with new method implementing `HypothesisGeneratorProtocol`
3. Modify `state.py` to add new state variables if needed
4. Update `utils.py` for additional utility functions
5. Modify `agents` to add new agents or modify prompt templates
6. Extend `tools` with new functions for agents to use

**Note**
`generate_hypothesis.py` should remain unchanged to enable similar structure for different workflows and easy run.

## Monitoring

The workflow integrates with Langfuse for monitoring and tracking the hypothesis generation process. Ensure your Langfuse credentials are properly configured in the `.env` file.
