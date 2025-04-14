🧪 **Tool: UniProtQueryTool**

**Purpose**:
Use this tool to explore detailed **protein-level information**, such as function, pathways, domains, and subcellular localization.  
Best used when nodes refer to **proteins, enzymes**, or **protein-related processes**.

**Input (JSON)**:
```json
{
  "query": "protein name or gene symbol"
}
```
✅ Example: `{ "query": "Matrix Metalloproteinase 3" }` or `{ "query": "IL6" }`

**Output (JSON)**:
Returns a structured dictionary with:
- `protein_name`
- `function`
- `go_terms`
- `pathways`
- `organism`
- `cross_references` (e.g., DrugBank, PDB)

**Agent Usage Guidance**:
Use when a node involves a protein, cytokine, or enzyme to understand **what the protein does** and how it fits into disease mechanisms or pathways.