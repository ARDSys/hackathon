import os

from firecrawl import FirecrawlApp


async def query_firecrawl(keyword: str) -> str:
    firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

    search_params = {
        "query": f"site:pubmed.ncbi.nlm.nih.gov {keyword}",
    }

    results = firecrawl.search(**search_params)

    return "\n".join([result for result in results["data"]])
