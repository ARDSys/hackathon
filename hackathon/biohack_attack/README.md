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

1. **Knowledge Integration Agent**
   - Aggregates data from multiple scientific sources
   - Maintains semantic consistency across different knowledge bases
   - Handles data normalization and entity resolution

2. **Hypothesis Generation Agent**
   - Uses advanced pattern recognition to identify potential relationships
   - Applies scientific reasoning to form initial hypotheses
   - Implements parallel processing for multiple hypothesis generation

3. **Verification Agent**
   - Decomposes hypotheses into testable statements
   - Conducts systematic literature reviews
   - Assigns confidence scores based on evidence quality

4. **Refinement Agent**
   - Analyzes verification results
   - Suggests hypothesis modifications
   - Implements iterative improvement cycles

5. **Quality Control Agent**
   - Monitors the entire hypothesis generation process
   - Ensures scientific rigor and methodological soundness
   - Maintains consistency across all generated hypotheses

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

### Environment Setup

- Create a `.env` file in the project root with the following required API keys:
   ```
   PUBMED_API_KEY=your_key
   SEMANTIC_SCHOLAR_API_KEY=your_key
   EUROPE_PMC_API_KEY=your_key
   ```
- Install the required packages:
   ```bash
   uv sync
   source .venv/bin/activate
   ```

## Usage

From the hackathon's root directory, run the `run.sh` script:

```bash
./run.sh
```
