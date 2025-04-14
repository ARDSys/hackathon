# BioHack Attack Hypothesis Generator

The solution created by BioHack Attack for the BeeARD x Google for Education.

Authors: Oleksii Furman, Filip Strózik, Zbigniew Tomanek, Patryk Wielopolski 

---

## BioHack Attack Approach

- 📚 Multi-Source Knowledge Integration
- 🧞‍♂️ Parallel Hypothesis Generation
- 🔍 Comprehensive Hypothesis Verification Framework
- 🔁 Iterative Hypothesis Refinement

### Multi Agent System Design

The BioHack Attack system employs a sophisticated multi-agent architecture to generate and validate scientific hypotheses. The system consists of the following specialized agents:

- **Hypothesis Generator**: Orchestrates the multi-step hypothesis generation process
- **Reference Agent**: Enhances a given scientific hypothesis by adding relevant references.
- **Ontology Agent**: Enriches knowledge graphs with information from external sources
- **Research Agents**: Specialized agents that query different scientific databases
- **Critic Agent**: Evaluates hypotheses against scientific criteria
- **Verification Agent**: Verifies individual statements against literature
- **Refiner Agent**: Improves hypotheses based on verification results

### 🧑‍💻 Data / API 💿

Article Datasets
- Pubmed
- Firecrawl
- BiorXiv
- Europe PMC
- Semantic Scholar

Knowledge Graphs
- Hetionet
- Prime KG

### Hypothesis Verification Framework

- 💁 Hypothesis decomposition into fundamental falsifiable statements
- 🔎 Individual statement verification through targeted literature searches
- ➖ Evidence classification into supporting vs. contradicting evidence
- 💪 Confidence scoring for each evidence item and statement
- 🎶 Multi-dimensional evaluation across 8 scientific criteria (novelty, feasibility, impact, falsifiability, testability, parsimony, explanatory power, predictive power)
- 👍 Aggregated verification synthesizing individual statement assessments into overall hypothesis validity
- 🤝 Quantitative scoring system for comparing hypothesis quality

## Technical Overview

The BioHack Attack system is built using a modern Python-based architecture with the following key components:

### Core Architecture
- **Modular Design**: The system is organized into distinct modules for knowledge graph processing, hypothesis generation, and verification
- **Asynchronous Processing**: Implements parallel processing for efficient hypothesis generation and verification
- **Data Pipeline**: Robust ETL pipeline for processing scientific literature and knowledge graphs

### Key Components
1. **Knowledge Graph Processing**
   - Entity resolution and relationship extraction
   - Graph-based pattern recognition
   - Semantic similarity calculations

2. **Hypothesis Generation Engine**
   - Pattern-based hypothesis formation
   - Scientific reasoning implementation
   - Multi-criteria optimization

3. **Verification System**
   - Automated literature review
   - Evidence scoring and classification
   - Confidence assessment algorithms

4. **Storage and Retrieval**
   - Efficient data structures for hypothesis storage
   - Fast retrieval mechanisms
   - Version control for hypothesis evolution

## Overview

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) package and project manager
- Python 3.11 or higher
- Access to required API keys for scientific databases

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
