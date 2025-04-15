import logging
import os
import time
from io import BytesIO
from itertools import chain
from pathlib import Path

import PyPDF2
import requests
from bs4 import BeautifulSoup
from langchain.tools.retriever import create_retriever_tool
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from requests.exceptions import RequestException

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://ncn.gov.pl"
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)


def fetch_html(url, max_retries=3, retry_delay=1):
    """Fetch HTML content with retry mechanism."""
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except RequestException as e:
            retries += 1
            if retries == max_retries:
                logger.error(f"Failed to fetch HTML after {max_retries} retries: {e}")
                raise
            logger.warning(f"Retry {retries}/{max_retries} after error: {e}")
            time.sleep(retry_delay * (2 ** (retries - 1)))


def parse_projects(html):
    """Parse HTML to extract project data."""
    soup = BeautifulSoup(html, "html.parser", from_encoding="utf-8")
    # Find all <tr> tags with a class that includes 'opus-nz'
    rows = soup.find_all("tr", class_=lambda x: x and "opus-nz" in x)
    projects = []
    for row in rows:
        classes = row.get("class")
        group = next((cls for cls in classes if cls.startswith("opus-nz")), None)
        td_polski = row.find("td", class_="polski")
        if td_polski:
            a_tag = td_polski.find("a")
            if a_tag:
                title = a_tag.get_text(strip=True)
                pdf_link = a_tag.get("href")
                if pdf_link.startswith("/"):
                    pdf_link = BASE_URL + pdf_link
                projects.append({"group": group, "title": title, "pdf_link": pdf_link})
    return projects


def fetch_pdf_content(pdf_url):
    """Download a PDF and extract its text content with caching."""
    filename = pdf_url.split("/")[-1]
    cache_path = CACHE_DIR / filename

    if cache_path.exists():
        logger.info(f"Loading PDF from cache: {cache_path}")
        pdf_data = cache_path.read_bytes()
    else:
        logger.info(f"Downloading PDF from: {pdf_url}")
        response = requests.get(pdf_url, headers=HEADERS)
        response.raise_for_status()
        pdf_data = response.content
        cache_path.write_bytes(pdf_data)

    with BytesIO(pdf_data) as f:
        reader = PyPDF2.PdfReader(f)
        content = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            content += page_text
    return content


def get_opus():
    """Fetch, parse, and process the opus documents."""
    html_url = "https://ncn.gov.pl/sites/default/files/listy-rankingowe/2024-03-15-oppr4giwi8/opus.html"
    html_content = fetch_html(html_url)
    projects = parse_projects(html_content)
    docs_list = []

    for project in projects:
        content = "Project Details:\n"
        content += f"Title: {project['title']}\n"
        try:
            pdf_text = fetch_pdf_content(project["pdf_link"])
            content += "Abstract: " + pdf_text
        except Exception as e:
            logger.error(f"Error fetching PDF for {project['title']}: {e}")
        docs_list.append(content)  # Append the content to docs_list

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=100, chunk_overlap=50
    )

    class TempDocClass:
        def __init__(self, page_content):
            self.page_content = page_content
            self.metadata = ""

    doc_splits = [
        TempDocClass(page_content=x)
        for x in chain.from_iterable(
            [text_splitter.split_text(doc) for doc in docs_list]
        )
    ]
    if not doc_splits:
        logger.error("No documents available to index. Please check extraction.")
        raise ValueError("Empty document list after splitting.")
    return doc_splits


if __name__ == "__main__":
    try:
        doc_splits = get_opus()
    except Exception as e:
        logger.error(f"Failed to process documents: {e}")
        raise

    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        collection_name="rag-ncn",
        embedding=OpenAIEmbeddings(),
    )
    retriever = vectorstore.as_retriever()

    query = """
*Hypothesis Overview:*
The proposed hypothesis states, "In patients with Systemic Lupus Erythematosus (SLE) showing elevated levels of Antinuclear Antibodies (ANA) and Interferon-alpha (IFN-α), the concurrent presence of viral infections promotes heightened differentiation of Th17 cells, which correlates with increased disease severity and the risk of developing Rheumatoid Arthritis (RA)."

#### Summary of Findings from Literature

1. *Direct Prior Coverage:*
   - While components of the hypothesis have been examined separately, such as the relationships between *ANA*, *IFN-α*, and Th17 cells in SLE, the specific interaction proposed—of viral infections exacerbating Th17 differentiation leading to increased SLE severity and subsequent development of RA—remains underexplored.
   - Literature addressing the relationship between viral infections and SLE often discusses their role as triggers for flares but lacks a comprehensive exploration of their impact on Th17 cell differentiation and subsequent RA development.

2. *New Conceptual Links:*
   - The hypothesis draws a novel connection between viral infections and Th17 differentiation in SLE patients, implying that viral infection does not merely act as a passive factor but instead actively contributes to the severity of the autoimmune response.
   - Furthermore, it proposes that SLE patients, already having a compromised immune state, are particularly vulnerable to the negative impacts of viral infections, providing a pathway that links autoimmunity to potential secondary autoimmune conditions like RA.

3. *Innovative Methodology or Framework:*
   - While the hypothesis leverages existing biomarkers and cytokines (e.g., ANA, IFN-α, Th17 cells), it calls for exploring novel frameworks for measuring these interactions. This could lead to innovative assessment methodologies to quantify relationships between viral load, Th17 activity, and inflammation markers in SLE patients.

4. *Challenge to Existing Paradigms:*
   - It questions the traditional understanding of how viral infections relate to autoimmune disease progression. The suggestion that viral infections can actively contribute to Th17 cell differentiation proposes a paradigm shift from viewing infections merely as co-morbidities to being integral in the pathogenesis of autoimmunity.

#### Gaps, Contradictions, and Absences in Existing Studies

- *Lack of Direct Evidence:*
  - No existing studies directly evaluate how viral infections in SLE influence Th17 cell differentiation or the development of RA, marking this hypothesis as a potentially significant departure from established knowledge.
- *Dual Role of Infections:*
  - The literature indicates mixed findings on how viral infections influence autoimmune processes—some studies identify them as exacerbating factors, while others suggest they can have protective roles, particularly pertaining to type I interferon responses.
- *Th17 Dynamics in SLE:*
  - Although studies have identified cytokine interplays involving Th17 cells in SLE, the comprehensive impact of concurrent infections has not been fully addressed, highlighting an important gap that this hypothesis seeks to explore.

### Conclusion

In conclusion, the evaluated hypothesis introduces significant novelty by linking viral infections to Th17 cell differentiation in SLE patients and correlating this with increased disease severity and the risk of developing RA. Although components of the hypothesis draw from established research in autoimmune disease mechanisms, the specific framework proposed is largely new and largely unexplored in existing literature.
    """
    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_blog_posts",
        f"Search and return information related to my hypothesis {query}",
    )

    tools = [retriever_tool]

    # Define application steps
    def retrieve(state):
        retrieved_docs = vectorstore.similarity_search(state["question"], k=5)
        logger.info("Retrieved documents:")
        for doc in retrieved_docs:
            print(doc.page_content)
