🧫 **Tool: EnsemblAPIManager**

**Purpose**:
Use this tool to fetch structured metadata for a **gene symbol**.  
It returns identifiers, synonyms, and related annotations.

**Input (JSON)**:
```json
{
  "gene_symbol": "official gene symbol"
}
```
✅ Example: `{ "gene_symbol": "IL6" }`

**Output (JSON)**:
Includes:
- `ensembl_id`
- `ncbi_id`
- `full_name`
- `biotype`
- `species`
- `aliases`

**Agent Usage Guidance**:
Use this tool when you encounter a **gene name** and want to normalize it or retrieve useful metadata.  
Often the first step in grounding a biological term before querying other tools like UniProt or DisGeNET.