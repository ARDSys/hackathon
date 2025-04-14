# 💡 Forging Validated Insights: Our Intelligence Engine

We commence with the intricate tapestry of a data subgraph – a promising, yet nascent, landscape of potential insights. But potential isn't enough. Our mission is to sculpt this raw potential into **rock-solid, empirically validated hypotheses** that command confidence.

---

### Phase 1: 🔗 Foundational Grounding - Every Link, Validated

Our core philosophy? **No connection left untethered from real-world evidence.** This meticulous grounding process is orchestrated by our bespoke AI agent:

1.  **Precision Query Generation:** For every single *edge* representing a relationship, our AI agent acts as a semantic distiller. It crafts hyper-focused **5-6 word conceptual summaries**, transforming abstract connections into potent search vectors.
2.  **Curated Knowledge Corpus:** These precise vectors retrieve a curated set of **10 highly relevant academic papers** 📚 *per edge*. This builds a dense, context-rich knowledge base meticulously mapped to every fundamental relationship in your graph.

---

### Phase 2: ✨ The Art of Differential Evidence Sampling - Engineering Unique Perspectives

Herein lies a stroke of engineered serendipity. Recognizing that monolithic evidence breeds monolithic thinking, we foster true intellectual diversity and robustness:

1.  **Evidence Stratification:** Each edge's dedicated 10-paper corpus is intelligently partitioned into two distinct **Evidence Strata** (groups of 5 papers).
2.  **Combinatorial Hypothesis Generation:** When constructing hypotheses spanning multiple edges, our engine performs **Differential Evidence Sampling**. It deliberately selects *one* specific evidence stratum for *each* edge involved.

> **The Payoff:** This elegant strategy guarantees that **every generated hypothesis is inherently unique**, forged from a subtly distinct combination of evidential foundations. We escape the echo chamber, ensuring a diverse exploration of the possibility space and dramatically increasing confidence in the resilience and validity of our final insights. It's testing hypotheses across a *spectrum* of curated evidence.

---

### Phase 3: 🏆 The Crucible of Evaluation - Where Hypotheses Compete

Generating diverse hypotheses is only the beginning. To identify the most promising, we subject them to a rigorous evaluation framework:

1.  **The Swiss Tournament Arena:** Hypotheses enter an intellectual gauntlet – a **Swiss tournament**. This highly efficient system enables robust pairwise comparisons, rapidly surfacing the strongest contenders from a large pool without exhaustive all-vs-all evaluation. Optimized survival of the fittest.
2.  **Bespoke Evaluation Metrics:** Victory isn't generic. We deploy **custom evaluation criteria** 🎯, tailored to domain nuances and the desired characteristics of a valuable hypothesis, rewarding genuine explanatory power and actionable potential.

---

### ✅ The Result: Intelligent Design Meets Rigorous Validation

Our process transcends simple graph analysis. It's an orchestrated workflow embedding empirical validation at its core, leveraging AI for precision, employing sophisticated sampling for diversity, and utilizing competitive evaluation for refinement.

> We transform complex subgraphs not just into insights, but into **high-confidence, robustly validated hypotheses ready for real-world application.**
>
> **This is data intelligence, evolved.**

## setup and run

pip install .
source .venv/bin/activate

Edit hackathon/modules/generators/TemplateGenerator.py and set the correct path to the subgraph.

python -m hackathon.modules.generators.TemplateGenerator