
# IL-23–MMP Axis as a Driver of Rheumatoid Arthritis-Associated Bone Loss

**Hypothesis ID:** b9795c220bc2a9659d0640c07e652bc2bd96c4bbc146c2b37127938045087e6d

**Subgraph ID:** 55d93cbcc225b166084d73d8e71f3ef21aeac51804532a5f9b698fcde97a33f7

We hypothesize that in rheumatoid arthritis, autoimmunity-induced dysregulation of the Th17 cell pathway elevates IL-23 levels, which in turn stimulate matrix metalloproteinase production. The resulting extracellular matrix degradation recruits fibroblast-like synoviocytes that amplify local pro-inflammatory cytokine expression, thereby activating osteoclast differentiation via the RANK/RANKL pathway and reducing bone mineral density. Targeting IL-23 or MMP activity may therefore complement RANKL inhibition (e.g., with Denosumab) to mitigate osteoporotic fractures.

## References
- T cell dysregulation in rheumatoid arthritis: Recent advances and natural product interventions. (2025) - Elsevier
- Identification of BHLHE40-Expressing CD4 T Cells Producing GM-CSF in Rheumatoid Arthritis. (2025) - John Wiley & Sons
- The IL-23R and Its Genetic Variants: A Hitherto Unforeseen Bridge Between the Immune System and Cancer Development. (2024) - PubMed
- Integrating transcriptomics and network pharmacology to reveal the effect and mechanism of Bai-Jie-Jing-Xie ointment on improving skin inflammation of psoriasis. (2025) - PubMed
- Neutrophil exhaustion and impaired functionality in psoriatic arthritis patients. (2024) - PubMed
- Matrix metalloproteinase-driven epithelial-mesenchymal transition: implications in health and disease. (2025) - PubMed
- Matrix Metalloproteinases in Ureteropelvic Junction Obstruction: Their Role in Pathogenesis and Their Use as Clinical Markers. (2025) - PubMed
- Interaction with hyaluronan matrix and miRNA cargo as contributors for in vitro potential of mesenchymal stem cell-derived extracellular vesicles in a model of human osteoarthritic synoviocytes. (2019) - PubMed
- The Role of Cell-Matrix Interactions in Connective Tissue Mechanics. (2021) - arXiv
- Mechanical stress overload promotes NF-κB/NLRP3-mediated osteoarthritis synovitis and fibrosis through Piezo1 (2025) - PubMed
- Fibroblast-like synoviocytes and their role in inflammatory joint diseases (2023) - PubMed
- ACT001 improves OVX-induced osteoporosis by suppressing the NF-κB/NLRP3 signaling pathway. (2025) - PubMed
- Osteoimmunology in Osteoarthritis: Unraveling the Interplay of Immunity, Inflammation, and Joint Degeneration. (2025) - PubMed
- Echinococcus granulosus promotes MAPK pathway-mediated osteoclast differentiation by inhibiting Nrf2 in osseous echinococcosis. (2025) - PubMed
- Duplications within exon 1 of TNFRSF11A encoding receptor activator of nuclear factor-kappa B (RANK) are associated with tendon avulsion. (2025) - PubMed
- Beyond Bone Remodeling: Denosumab's Multisystemic Benefits in Musculoskeletal Health, Metabolism, and Age-Related Diseases-A Narrative Review. (2025) - PubMed
- Colla Carapacis et Plastri ameliorates postmenopausal osteoporosis and macrophage immunity by modulating the RANK/RANKL/OPG signaling pathway in ovariectomized rats. (2025) - PubMed
- Moringa oleifera: Exploring the Potential in Managing Bone Loss: Insights from Preclinical Studies. (2025) - PubMed
- RANK/RANKL Signaling Pathway in Breast Development and Cancer. (2025) - PubMed
- Colla Carapacis et Plastri ameliorates postmenopausal osteoporosis and macrophage immunity by modulating the RANK/RANKL/OPG signaling pathway in ovariectomized rats. (2025) - PubMed
- Denosumab use reduces risk of rheumatoid arthritis in patients with osteoporosis. (2024) - PubMed
- Denosumab: an effective treatment for reducing the risk of fractures in patients with osteoporosis. (2023) - PubMed
- Comparison of different intervention thresholds for the treatment of glucocorticoid-induced osteoporosis: a cross-sectional study. (2025) - PubMed
- Ultra-Processed Food and Its Impact on Bone Health and Joint Diseases: A Scoping Review. (2025) - PubMed

## Context
None

## Subgraph
```
(Autoimmunity)-[:`is associated with a dysregulation in the`]->(`Th17 cell pathway`),
(`Th17 cell pathway`)-[:`is modulated by the cytokine`]->(`Interleukin-23 (IL-23)`),
(`Interleukin-23 (IL-23)`)-[:`stimulates the production of`]->(`Matrix metalloproteinases (MMPs)`),
(`Matrix metalloproteinases (MMPs)`)-[:`are involved in the degradation of`]->(`extracellular matrix components`),
(`extracellular matrix components`)-[:`play a role in the recruitment of`]->(`fibroblast-like synoviocytes (FLS)`),
(`fibroblast-like synoviocytes (FLS)`)-[:`contribute to the expression of`]->(`pro-inflammatory cytokines`),
(`pro-inflammatory cytokines`)-[:`activate signaling pathways leading to`]->(`osteoclast differentiation`),
(`osteoclast differentiation`)-[:`leads to increased resorption of`]->(`bone tissue`),
(`bone tissue`)-[:`undergoes remodeling mediated by`]->(`RANK/RANKL pathway`),
(`RANK/RANKL pathway`)-[:`is inhibited by the administration of`]->(Denosumab),
(Denosumab)-[:`reduces the incidence of`]->(`osteoporotic fractures in patients with rheumatoid arthritis`),
(`osteoporotic fractures in patients with rheumatoid arthritis`)-[:`are characterized by a reduction in`]->(`bone mineral density (BMD)`),
(`Matrix metalloproteinases (MMPs)`)-[:`facilitate the turnover of`]->(`bone tissue`),
(Autoimmunity)-[:`induces imbalances in`]->(`pro-inflammatory cytokines`),
(`Interleukin-23 (IL-23)`)-[:`promotes the activity of`]->(`fibroblast-like synoviocytes (FLS)`),
(`fibroblast-like synoviocytes (FLS)`)-[:`interact with the`]->(`RANK/RANKL pathway`),
(`Th17 cell pathway`)-[:`influences the expression of`]->(`RANK/RANKL pathway`),
(`bone mineral density (BMD)`)-[:`is indirectly maintained by the presence of`]->(`extracellular matrix components`),
(`osteoclast differentiation`)-[:`is potentiated by the`]->(`Th17 cell pathway`),
(Denosumab)-[:`modulates the production of`]->(`Matrix metalloproteinases (MMPs)`),
(`bone tissue`)-[:`is structurally supported by`]->(`extracellular matrix components`),
(`pro-inflammatory cytokines`)-[:`are elevated in conditions of`]->(`low bone mineral density (BMD)`)
```
