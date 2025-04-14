"""Util that calls Arxiv."""
import logging
import os
from typing import Any, Dict, List, Optional, Annotated

from pydantic import BaseModel, Field, field_validator, model_validator
from langchain.schema import Document
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import InjectedState
from langchain_core.tools import InjectedToolCallId


logger = logging.getLogger(__name__)


class ArxivAPIWrapper(BaseModel):
    """Wrapper around ArxivAPI.

    To use, you should have the ``arxiv`` python package installed.
    https://lukasschwab.me/arxiv.py/index.html
    This wrapper will use the Arxiv API to conduct searches and
    fetch document summaries. By default, it will return the document summaries
    of the top-k results.
    It limits the Document content by doc_content_chars_max.
    Set doc_content_chars_max=None if you don't want to limit the content size.

    Attributes:
        top_k_results: number of the top-scored document used for the arxiv tool
        ARXIV_MAX_QUERY_LENGTH: the cut limit on the query used for the arxiv tool.
        load_max_docs: a limit to the number of loaded documents
        load_all_available_meta:
            if True: the `metadata` of the loaded Documents contains all available
            meta info (see https://lukasschwab.me/arxiv.py/index.html#Result),
            if False: the `metadata` contains only the published date, title,
            authors and summary.
        doc_content_chars_max: an optional cut limit for the length of a document's
            content

    Example:
        .. code-block:: python

            from langchain.utilities.arxiv import ArxivAPIWrapper
            arxiv = ArxivAPIWrapper(
                top_k_results = 3,
                ARXIV_MAX_QUERY_LENGTH = 300,
                load_max_docs = 3,
                load_all_available_meta = False,
                doc_content_chars_max = 40000
            )
            arxiv.run("tree of thought llm)
    """

    arxiv_search: Any = None #: :meta private:
    arxiv_exceptions: Any = "not_found" #: :meta private:
    top_k_results: int = 10
    ARXIV_MAX_QUERY_LENGTH: int = 300
    load_max_docs: int = 100
    load_all_available_meta: bool = False
    doc_content_chars_max: Optional[int] = 4000
    mindate: str = None
    maxdate: str = None

    @model_validator(mode="after")
    def validate_environment(self) -> "ArxivAPIWrapper":
        try:
            import arxiv
            self.arxiv_search = arxiv.Search
            self.arxiv_exceptions = (
                arxiv.ArxivError,
                arxiv.UnexpectedEmptyPageError,
                arxiv.HTTPError,
            )
        except ImportError:
            raise ImportError(
                "Could not import arxiv python package. "
                "Please install it with `pip install arxiv`."
            )
        return self

    def run(self, query: str) -> str:
        """
        Performs an arxiv search and A single string
        with the publish date, title, authors, and summary
        for each article separated by two newlines.

        If an error occurs or no documents found, error text
        is returned instead. Wrapper for
        https://lukasschwab.me/arxiv.py/index.html#Search

        Args:
            query: a plaintext search query
        """  # noqa: E501
        try:
            query = query[: self.ARXIV_MAX_QUERY_LENGTH]
            results = self.arxiv_search(  # type: ignore
                query, max_results=self.top_k_results
            ).results()
        except self.arxiv_exceptions as ex:
            return f"Arxiv exception: {ex}"
        docs = [
            f"Published: {result.updated.date()}\n"
            f"Title: {result.title}\n"
            f"Authors: {', '.join(a.name for a in result.authors)}\n"
            f"Summary: {result.summary}"
            for result in results
        ]
        if docs:
            return "\n\n".join(docs)[: self.doc_content_chars_max]
        else:
            return "No good Arxiv Result was found"

    def load(self, query: str) -> List[Document]:
        """
        Run Arxiv search and get the article texts plus the article meta information.
        See https://lukasschwab.me/arxiv.py/index.html#Search

        Returns: a list of documents with the document.page_content in text format

        Performs an arxiv search, downloads the top k results as PDFs, loads
        them as Documents, and returns them in a List.

        Args:
            query: a plaintext search query
        """  # noqa: E501
        try:
            import fitz
        except ImportError:
            raise ImportError(
                "PyMuPDF package not found, please install it with "
                "`pip install pymupdf`"
            )

        try:
            # Remove the ":" and "-" from the query, as they can cause search problems
            query = query.replace(":", "").replace("-", "")
            results = self.arxiv_search(  # type: ignore
                query[: self.ARXIV_MAX_QUERY_LENGTH], max_results=self.load_max_docs
            ).results()
        except self.arxiv_exceptions as ex:
            logger.debug("Error on arxiv: %s", ex)
            return []

        docs: List[Document] = []
        for result in results:
            try:
                doc_file_name: str = result.download_pdf()
                with fitz.open(doc_file_name) as doc_file:
                    text: str = "".join(page.get_text() for page in doc_file)
            except (FileNotFoundError, fitz.fitz.FileDataError) as f_ex:
                logger.debug(f_ex)
                continue
            if self.load_all_available_meta:
                extra_metadata = {
                    "entry_id": result.entry_id,
                    "published_first_time": str(result.published.date()),
                    "comment": result.comment,
                    "journal_ref": result.journal_ref,
                    "doi": result.doi,
                    "primary_category": result.primary_category,
                    "categories": result.categories,
                    "links": [link.href for link in result.links],
                }
            else:
                extra_metadata = {}
            metadata = {
                "Published": str(result.updated.date()),
                "Title": result.title,
                "Authors": ", ".join(a.name for a in result.authors),
                "Summary": result.summary,
                **extra_metadata,
            }
            doc = Document(
                page_content=text[: self.doc_content_chars_max], metadata=metadata
            )
            docs.append(doc)
            os.remove(doc_file_name)
        return docs


# Initialize ArXiv wrapper
arxiv_wrapper = ArxivAPIWrapper()


@tool("arxiv_tool", parse_docstring=True, return_direct=False)
def arxiv_tool(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Searches the arXiv API for scientific papers related to a given query.

    Useful for answering questions related to physics, computer science, mathematics,
    quantitative biology, quantitative finance, statistics, and other academic topics
    based on scientific preprints from arXiv.

    Args:
        query: A search query related to scientific research.

    Returns:
        A dictionary with information about the retrieved papers.
    """
    result = arxiv_wrapper.run(query)

    if "No good Arxiv Result was found" in result or "Arxiv exception" in result:
        return {
            "error": f"No good arXiv results found for '{query}'.",
            "papers": []
        }

    return {
        "papers": result
    }
