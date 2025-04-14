🔬 **Tool: BioRxivAPIManager**

**Purpose**:
Use this tool to search for recent scientific preprints from bioRxiv and medRxiv.  
It is best suited for retrieving **emerging or novel evidence** related to biological entities or relationships in the graph.

**Input (JSON)**:
```json
{
  "query": "search term or phrase"
}
```
✅ Example: `{ "query": "T-cell dysfunction in rheumatoid arthritis" }`

**Output (JSON)**:
A list of preprints with:
- `title`: The article title
- `authors`: First author or author string
- `date`: Publication date
- `abstract`: A brief summary
- `doi_url`: Link to the full article

**Agent Usage Guidance**:
Use this tool when a node represents a **biological process**, **pathway**, or **emerging concept** (e.g., "Elevated Serum Amyloid A").  
It helps gather supporting evidence and enriches reasoning with fresh literature.