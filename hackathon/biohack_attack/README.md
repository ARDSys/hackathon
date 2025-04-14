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

<TO BE GENERATED>

### 🧑‍💻 Data / API 💿

Artile Datasets
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

<TO BE DESCRIBED>

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
