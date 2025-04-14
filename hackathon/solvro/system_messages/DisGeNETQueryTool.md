🧬 **Tool: DisGeNETQueryTool**

**Purpose**:
Use this tool to retrieve known associations between **genes** and **diseases**.  
Best suited for nodes that are **genes** or **diseases**, especially those related to immunology or rheumatology.

**Input (JSON)**:
```json
{
  "gene_ncbi_id": "NCBI Gene ID as a string"
}
```
✅ Example: `{ "gene_ncbi_id": "5781" }` for gene PTPN22

**Output (JSON)**:
Returns a list of disease associations, including:
- `diseaseName`
- `diseaseUMLSCUI`
- `score`: Confidence or relevance score
- `pubmed_articles`: Optional supporting literature (if chained)

**Agent Usage Guidance**:
Use when you see a **gene node** and want to understand its disease connections.  
This helps explain how a gene is implicated in the disease mechanisms presented in the graph.