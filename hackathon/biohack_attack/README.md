# Sample Hypothesis Generator Template

This is a minimal template you can use as a starting point for building your own hypothesis generation system. It provides a basic structure that you can extend to implement your custom multi-agent system.

## Overview

The template consists of these minimal components:
- `generate_hypothesis.py`: CLI interface for running the hypothesis generation
- `hypothesis_generator.py`: A wrapper implementing the `HypothesisGeneratorProtocol`

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) package and project manager

## Environment Setup

1. Create a `.env` file in the project root with any API keys you might need, for example:
   ```
   # OpenAI
   OPENAI_API_KEY=your-api-key

   # Any other providers you plan to use
   ```

## Installation

Install the packages in the ARD's root directory:
```bash
uv sync
source .venv/bin/activate
```

## Usage

The template can be run using the `generate_hypothesis.py` script.
From the ARD's root directory:

```bash
python -m hackathon.sample.generate_hypothesis -f path/to/subgraph.json --output output_directory
```

### Arguments

- `--file` or `-f`: Path to the input JSON file containing the subgraph data
- `--output` or `-o`: Path to the output directory (defaults to current directory)

## Output

The output is a JSON file containing the hypothesis.
```json
{
    "title": "<hypothesis.title>",
    "text": "<hypothesis.statement>",
    "source": "<source_subgraph_as_json>",
    "metadata": {
        ... # all additional data from the hypothesis
    }
}
```

## Architecture

This template provides a minimal starting point:
1. Takes a subgraph as input
2. Processes it through a simple `HypothesisGenerator` implementation
3. Creates a Hypothesis object with basic information
4. Saves the Hypothesis to the output directory

## Development

To build your solution:
1. Modify `hypothesis_generator.py` to implement your multi-agent system approach
2. Add any necessary components for your solution (agents, tools, etc.)
3. Ensure your implementation follows the `HypothesisGeneratorProtocol`

**Note** 
`generate_hypothesis.py` should remain unchanged to enable similar structure across different implementations and easy testing.

## Extending this Template

Some ideas for extending this template:
1. Add agent definitions for different roles in your system
2. Implement tools and functions for your agents to use
3. Create a structured workflow between your agents
4. Add logging and monitoring capabilities
5. Integrate specialized knowledge sources or external APIs