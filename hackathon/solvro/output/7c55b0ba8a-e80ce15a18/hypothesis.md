
# Synergistic Targeting of BTK and Smoking-Induced TNF-α Pathways to Mitigate Joint Damage in RA

**Hypothesis ID:** e80ce15a18bc4600bfb440699917231cee63a351d2bae62657c3cb70b844ca6a

**Subgraph ID:** 7c55b0ba8a2f19cf09c39ec4f282fe527c8641f1fca49c12c862407d572c3def

We hypothesize that in rheumatoid arthritis, BTK inhibitors not only suppress B cell receptor‐mediated autoantibody production but also counteract smoking-induced epigenetic modifications in T cells that elevate TNF-α. This reduction in TNF-α levels is expected to attenuate NF-κB activation, thereby decreasing MMP expression in synovial fibroblasts, ultimately reducing cartilage extracellular matrix degradation, joint damage, and bone resorption. Testing this dual mechanism may provide a synergistic therapeutic strategy for RA.

## References
- Rilzabrutinib for the Treatment of Immune Thrombocytopenia. (2025) - European Journal of Haematology
- Aberrantly Expressed Mitochondrial Lipid Kinase, AGK, Activates JAK2-Histone H3 Axis and BCR Signal: A Mechanistic Study with Implication in CLL Therapy. (2024) - American Association for Cancer Research
- Targeting Tumor Microenvironment Interactions in Chronic Lymphocytic Leukemia Using Leukotriene Inhibitors. (2025) - Clinical Cancer Research
- BTK inhibitors enhance NKG2D ligand expression by regulating IL-10/STAT3 pathway in activated non-GCB diffuse large B-cell lymphoma cells. (2025) - Wolters Kluwer Health
- Novel Bruton's tyrosine kinase inhibitor TAS5315 suppresses the progression of inflammation and joint destruction in rodent collagen-induced arthritis. (2023) - PubMed
- TLR9 signalling in HCV-associated atypical memory B cells triggers Th1 and rheumatoid factor autoantibodies in chronic hepatitis C. (2019) - PubMed
- Recent Advances in Understanding the Pathogenesis of Rheumatoid Arthritis: New Treatment Strategies (2021) - PubMed
- Cochlin-Expressing Memory B (COMB) Cells Are Enriched in Autoimmune Diseases and Display a Distinct Activation Profile (2025) - PubMed
- Epigenetics in Multiple Sclerosis (2023) - PubMed
- The Aberrant Epigenetic Modifications in the Pathogenesis of Psoriasis (2018) - PubMed
- TNF-Alpha Inhibitor Prevents Cigarette Smoke Extract-Induced Cell Death in Osteoarthritis-Derived Chondrocytes in Culture. (2025) - PubMed
- Changes in Concentration of Selected Biomarkers of Exposure in Users of Classic Cigarettes, E-Cigarettes, and Heated Tobacco Products-A Narrative Review. (2025) - PubMed
- Sputum SLC40A1 as a Novel Biomarker is Increased in Patients with Acute Exacerbation of Chronic Obstructive Pulmonary Disease. (2025) - PubMed
- The Immune Base Therapy of Pain with Magnesium Sulfate on the Trigger Axis of the TNF-α-TRAF6-NF-κB and Its Inhibitor (miR-146a-5p) in Rats. (2025) - PubMed
- Integrating Serum Pharmacochemistry With Network Pharmacology to Elucidate the Mechanism of Wushen Decoction in the Prevention and Treatment of Lower Extremity Erysipelas. (2025) - PubMed
- PD-1 suppression enhances HIV reactivation and T-cell immunity via MAPK/NF-kB signaling. (2025) - PubMed
- Gentiopicroside attenuates collagen-induced arthritis in mice via modulating the CD147/p38/NF-κB pathway. (2022) - PubMed
- Zhuanggu Jianxi Decoction reduces synovial tissue inflammation in human knee osteoarthritis by regulating LXRs/NF-κB signaling pathway. (2021) - PubMed
- An injectable, self-healing and MMP-inhibiting hyaluronic acid gel via iron coordination. (2021) - arXiv
- IL-40 is up-regulated in the synovial fluid and cartilage of osteoarthritis patients and contributes to the alteration of chondrocytes phenotype in vitro. (2024) - PubMed
- A novel small molecule screening assay using normal human chondrocytes toward osteoarthritis drug discovery. (2024) - PubMed
- Nasal Chondrocytes Intensively Invade and Repair Pathologically Altered Cartilage Through Intrinsic Genomic Mechanisms: A Narrative Review. (2025) - PubMed
- Metabolic Reprogramming in Stromal and Immune Cells in Rheumatoid Arthritis and Osteoarthritis: Therapeutic Possibilities. (2025) - European Journal of Immunology
- Ugonin P facilitates chondrogenic properties in chondrocytes by inhibiting miR-3074-5p production: implications for the treatment of arthritic disorders. (2025) - Journal of Ethnopharmacology
- Application of Cartilage Extracellular Matrix to Enhance Therapeutic Efficacy of Methotrexate. (2023) - Korean Tissue Engineering and Regenerative Medicine Society
- A cross sectional study of bone and cartilage biomarkers: correlation with structural damage in rheumatoid arthritis. (2012) - PubMed

## Context
None

## Subgraph
```
(`BTK Inhibitors`)-[:target]->(`Bruton's Tyrosine Kinase (BTK)`),
(`Bruton's Tyrosine Kinase (BTK)`)-[:`is associated with`]->(`B cell receptor signaling pathway`),
(`B cell receptor signaling pathway`)-[:`is involved in`]->(`autoantibody production in rheumatoid arthritis`),
(`autoantibody production in rheumatoid arthritis`)-[:`is influenced by`]->(`epigenetic modifications in T cells`),
(`epigenetic modifications in T cells`)-[:`are influenced by`]->(`environmental factors such as smoking`),
(`environmental factors such as smoking`)-[:`increase the production of`]->(`pro-inflammatory cytokines like TNF-alpha`),
(`pro-inflammatory cytokines like TNF-alpha`)-[:activate]->(`NF-kappa B signaling pathway`),
(`NF-kappa B signaling pathway`)-[:modulates]->(`expression of matrix metalloproteinases (MMPs) in synovial fibroblasts`),
(`expression of matrix metalloproteinases (MMPs) in synovial fibroblasts`)-[:`contributes to`]->(`degradation of cartilage extracellular matrix in joint tissue`),
(`degradation of cartilage extracellular matrix in joint tissue`)-[:`leads to`]->(`joint damage and deformities in rheumatoid arthritis`),
(`joint damage and deformities in rheumatoid arthritis`)-[:`correlate with`]->(`increased bone resorption markers like CTX-I in serum`),
(`environmental factors such as smoking`)-[:exacerbate]->(`joint damage and deformities in rheumatoid arthritis`),
(`environmental factors such as smoking`)-[:promote]->(`degradation of cartilage extracellular matrix in joint tissue`),
(`epigenetic modifications in T cells`)-[:impact]->(`degradation of cartilage extracellular matrix in joint tissue`),
(`Bruton's Tyrosine Kinase (BTK)`)-[:influences]->(`autoantibody production in rheumatoid arthritis`),
(`expression of matrix metalloproteinases (MMPs) in synovial fibroblasts`)-[:`is affected by`]->(`pro-inflammatory cytokines like TNF-alpha`),
(`BTK Inhibitors`)-[:`indirectly reduce`]->(`joint damage and deformities in rheumatoid arthritis`),
(`BTK Inhibitors`)-[:reduce]->(`NF-kappa B signaling pathway`),
(`B cell receptor signaling pathway`)-[:enhances]->(`NF-kappa B signaling pathway`),
(`increased bone resorption markers like CTX-I in serum`)-[:`are elevated due to`]->(`pro-inflammatory cytokines like TNF-alpha`),
(`NF-kappa B signaling pathway`)-[:enhances]->(`increased bone resorption markers like CTX-I in serum`)
```
