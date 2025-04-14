import os
import random
import time
import urllib.error
import urllib.request

from langchain_community.tools.pubmed.tool import PubmedQueryRun
from langchain_community.utilities.pubmed import PubMedAPIWrapper
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import InjectedState
from langchain_core.tools import InjectedToolCallId
from typing import Annotated


class PubMedAPIWrapperImproved(PubMedAPIWrapper):
    def retrieve_article(self, uid: str, webenv: str) -> dict:
        url = (
            self.base_url_efetch
            + "db=pubmed&retmode=xml&id="
            + uid
            + "&webenv="
            + webenv
        )
        if self.api_key != "":
            url += f"&api_key={self.api_key}"

        retry = 0
        while True:
            try:
                result = urllib.request.urlopen(url)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and retry < self.max_retry:
                    # Too Many Requests errors
                    # wait for an exponentially increasing amount of time
                    sleep_time_random = random.uniform(0.5, 1.5)
                    sleep_time = self.sleep_time + sleep_time_random
                    print(  # noqa: T201
                        f"Too Many Requests, waiting for {sleep_time:.2f} seconds..."
                    )
                    time.sleep(sleep_time)
                    self.sleep_time *= 2
                    retry += 1
                else:
                    raise e

        xml_text = result.read().decode("utf-8")
        text_dict = self.parse(xml_text)
        return self._parse_article(uid, text_dict)



# Initialize the PubMed API wrapper
pubmed_api_wrapper = PubMedAPIWrapperImproved(api_key=os.getenv("PUBMED_API_KEY"))

@tool("pub_med", parse_docstring=True)
def pubmed_tool(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
    config: RunnableConfig = None,
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """
    A wrapper around PubMed.
    Useful for when you need to answer questions about medicine, health,
    and biomedical topics from biomedical literature, MEDLINE, life science journals, and online books.
    
    Args:
        query: A search query for PubMed articles.
        tool_call_id: Injected tool call ID.
        config: Runnable configuration.
        state: Injected state.
    """
    return pubmed_api_wrapper.run(query)
