from langchain.tools import tool
from langchain_community.chat_models import ChatPerplexity
from langchain_core.messages import HumanMessage


@tool
def search_perplexity(query: str) -> str:
    """Search Perplexity for relevant literature with accurate citations.

    Args:
        query: The search query to find relevant literature

    Returns:
        A string containing the search results from Perplexity with citations
    """
    chat = ChatPerplexity()
    prompt = f"""Please search for information about: {query}
    Please provide a comprehensive response with accurate citations to sources. 
    Include specific references and links where possible."""
    messages = [HumanMessage(content=prompt)]
    response = chat.invoke(messages)
    sources = "\n".join(
        [
            f"{i + 1}. {source}"
            for i, source in enumerate(response.additional_kwargs["citations"])
        ]
    )

    resp = f"""
    {response.content}

    Sources:
    {sources}
    """

    return resp
