# ARD (Autonomous Research Discovery)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

ARD is a Python package for building, curating, and mining knowledge graphs to enable autonomous research discovery. It's part of the [BeeARD ecosystem](https://beeard.ai) that aims to accelerate scientific progress through AI-driven hypothesis generation and validation.

## 🚀 Features

- **Knowledge Graph Management**: Build and maintain comprehensive knowledge graphs from scientific literature
- **Multi-Agent Systems**: Leverage both AutoGen and LangGraph implementations for hypothesis generation
- **Subgraph Mining**: Extract and analyze meaningful subgraphs for research insights
- **Hypothesis Generation**: Generate novel research hypotheses using advanced LLM-based agents
- **CLI Interface**: Command-line tools for common knowledge graph operations

## 📦 Installation

ARD requires Python 3.12+ and uses [UV](https://github.com/astral-sh/uv) as its package manager.

```bash
# Clone the repository
git clone https://github.com/ARDSys/hackathon.git .
cd hackathon

# Create virtual env
uv sync
source .venv/bin/activate

# Install in development mode
uv pip install -e .
```

## 🛠️ Usage

### Building Knowledge Graphs

```python
from ard.knowledge_graph import KnowledgeGraph
from ard.data import DatasetItem

# Initialize a knowledge graph
kg = KnowledgeGraph()

# Add data and build relationships
# ... (see examples/ for detailed usage)
```

### Generating Hypotheses

ARD provides two workflow implementations for hypothesis generation:

1. **AutoGen-based Workflow**:

```python
from hackathon.autogen import generate_hypothesis

# Generate hypotheses using AutoGen agents
hypothesis = generate_hypothesis.run(subgraph, output_dir="results")
# Access hypothesis properties: hypothesis.title, hypothesis.statement, hypothesis.references, etc.
```

2. **LangGraph-based Workflow**:

```python
from hackathon.langgraph import generate_hypothesis

# Generate hypotheses using LangGraph agents
hypothesis = generate_hypothesis.run(subgraph, output_dir="results")
# Access hypothesis properties: hypothesis.title, hypothesis.statement, hypothesis.references, etc.
```

### CLI Usage

```bash
# Create a knowledge graph
ard graph --data-path /path/to/data --output knowledge_graph.pkl

# Extract subgraphs
ard subgraph --graph-path knowledge_graph.pkl --output-dir output
```

## 🏗️ Architecture

ARD is organized into several key components:

- **knowledge_graph/**: Core knowledge graph implementation and management
- **subgraph/**: Subgraph extraction and analysis tools
- **hypothesis/**: Hypothesis generation and validation
- **data/**: Data ingestion and management
- **llm/**: LLM integration utilities
- **utils/**: Common utilities and helpers
- **storage/**: Storage backends and persistence

## 📚 Documentation

For detailed documentation, visit [docs.beeard.ai](https://docs.beeard.ai/).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
