# BioHack Attack: Advanced Rheumatology Hypothesis Generator

BioHack Attack is a sophisticated AI-powered hypothesis generation system for rheumatology research. The system uses a multi-agent architecture to analyze knowledge graphs, explore biomedical literature, and generate novel, testable research hypotheses.

## Overview

This system combines multiple specialized agents to:

1. Analyze knowledge graph subgraphs related to rheumatology concepts
2. Enrich the subgraphs with information from scientific databases
3. Generate initial hypotheses based on the enriched knowledge
4. Decompose hypotheses into falsifiable statements
5. Verify each statement against scientific literature
6. Refine hypotheses through multiple iterations
7. Produce well-structured, scientifically sound research proposals

## Architecture

BioHack Attack consists of several components:

### Core Components

- **Hypothesis Generator**: Orchestrates the multi-step hypothesis generation process
- **Reference Agent**: Enhances a given scientific hypothesis by adding relevant references.
- **Ontology Agent**: Enriches knowledge graphs with information from external sources
- **Research Agents**: Specialized agents that query different scientific databases
- **Critic Agent**: Evaluates hypotheses against scientific criteria
- **Verification Agent**: Verifies individual statements against literature
- **Refiner Agent**: Improves hypotheses based on verification results

### Research Agents

The system includes specialized agents for querying various scientific data sources:

- **PubMed Agent**: Searches peer-reviewed literature
- **BioRxiv Agent**: Searches preprints
- **Europe PMC Agent**: Searches open access literature
- **Semantic Scholar Agent**: Analyzes citation networks
- **Hetionet Agent**: Queries biomedical knowledge graphs
- **Firecrawl Agent**: Performs multi-source scientific web searches

## Getting Started

### Installation

1. Install dependencies:
```bash
# Setup virtual env
uv sync
source .venv/bin/activate

# Install in development mode
uv pip install -e .
```

3. Create a `.env` file with your API keys:
```
export GEMINI_API_KEY=<GEMINI_API_KEY>
export OPENAI_API_KEY=<OPENAI_API_KEY>
export FIRECRAWL_API_KEY=<FIRECRAWL_API_KEY>
```

### Usage

#### Basic Usage

Run the hypothesis generator with a knowledge graph subgraph:

```bash
python generate_hypothesis.py example_subgraph.json \
    --output custom_output \
    --num-hypotheses 10 \
    --num-threads 8 \
    --top-k 3 \
    --max-iterations 5 \
    --debug-log
```

#### Advanced Configuration

```bash
PYTHONPATH="./:$PYTHONPATH" uv run biohack_attack/generate_hypothesis.py \
  ../evaluation/Autoimmunity.json \
  --output custom_output_dir \
  --num-hypotheses 5 \
  --num-threads 8 \
  --top-k 3 \
  --max-iterations 2
```

### Parameters

- `input_file`: Path to the input subgraph JSON file
- `--output`: Base directory for output files
- `--num-hypotheses`: Number of initial hypotheses to generate
- `--num-threads`: Number of threads for parallel processing
- `--top-k`: Number of top hypotheses to refine in each iteration
- `--max-iterations`: Maximum number of refinement iterations
- `--debug-log/--no-debug-log`: Enable/disable debug logging
- `--info-log/--no-info-log`: Enable/disable info logging

## Output Structure

The output includes:

- **JSON hypothesis file**: Structured representation of the hypothesis
- **Markdown hypothesis file**: Human-readable version of the hypothesis
- **Logs directory**: Contains detailed logs of the generation process
- **Process state file**: JSON file with the complete state of the generation process

## Project Structure

```
biohack_attack/
├── hackathon_agents/           # Core agents for hypothesis generation
│   ├── research_agents/        # Specialized research database agents
│   │   ├── biorxiv_agent.py
│   │   ├── pubmed_agent.py
│   │   └── ...
│   ├── decomposition_agent.py  # Hypothesis decomposition
│   ├── hypothesis_agent.py     # Base hypothesis generation
│   ├── refiner_agent.py        # Hypothesis refinement
│   ├── verification_agent.py   # Hypothesis verification
│   └── ...
├── tools/                      # Tools for interacting with external APIs
│   ├── hetionet.py
│   ├── firecrawl_tool.py
│   ├── search_api_tools.py
│   └── ...
├── generate_hypothesis.py      # Main entry point
├── hypothesis_generator.py     # Core orchestration logic
├── model.py                    # Data models
└── model_factory.py            # LLM configuration
```

- This project was developed during the Hackathon 2025
- Thanks to all contributors and the community