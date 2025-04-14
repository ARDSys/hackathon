# AutoGen Workflow

This workflow implements a hypothesis generation system using AutoGen, designed to analyze subgraphs and generate scientific hypotheses through multi-agent collaboration.

## Overview

The workflow consists of several key components:

- `generate_hypothesis.py`: CLI interface for running the hypothesis generation
- `hypothesis_generator.py`: Main logic for hypothesis generation using AutoGen
- `groupchat.py`: Manages the multi-agent conversation flow
- `agents.py`: Defines the specialized agents for the workflow
- `prompts.py`: Contains prompt templates for the agents
- `functions.py`: Defines the tools and functions available to agents
- `llm_config.py`: Configuration for LLM providers
- `langfuse.py`: Integration with Langfuse for monitoring

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

   # OpenTelemetry
   OTEL_EXPORTER_OTLP_ENDPOINT=https://cloud.langfuse.com/api/public/otel
   OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic sk-lf-123
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
python -m hackathon.autogen.generate_hypothesis -f data/Bridge_Therapy.json --output hackathon/autogen/output
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

The workflow uses AutoGen to create a multi-agent system for hypothesis generation:

1. Takes a subgraph as input
2. Initializes specialized agents with specific roles and capabilities
3. Manages a group chat between agents to collaboratively generate hypotheses
4. Processes the conversation to extract and refine the final hypothesis
5. Saves the Hypothesis to the output directory

## Development

To modify or extend the workflow:

1. Edit `agents.py` to modify agent configurations and roles
2. Update `prompts.py` to modify agent prompts and templates
3. Modify `functions.py` to add new tools and capabilities
4. Update `groupchat.py` to modify the conversation flow
5. Extend `hypothesis_generator.py` with new generation methods

**Note**
`generate_hypothesis.py` should remain unchanged to enable similar structure for different workflows and easy run.

## Monitoring

The workflow integrates with Langfuse for monitoring and tracking the hypothesis generation process. Ensure your Langfuse credentials are properly configured in the `.env` file.
