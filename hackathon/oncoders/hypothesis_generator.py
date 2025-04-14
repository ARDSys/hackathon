import json
from typing import Any

from autogen import OpenAIWrapper
from langfuse.callback import CallbackHandler
from pydantic import BaseModel

from ard.hypothesis import Hypothesis, HypothesisGeneratorProtocol
from ard.subgraph import Subgraph

from .groupchat import create_group_chat
from .llm_config import get_llm_config

langfuse_callback = CallbackHandler()


class HypgenResult(BaseModel):
    title: str
    statement: str


class Reference(BaseModel):
    title: str
    url: str
    summary: str


class ReferenceList(BaseModel):
    references: list[Reference]


class HypothesisGenerator(HypothesisGeneratorProtocol):
    def run(self, subgraph: Subgraph) -> Hypothesis:
        # Initialize Langfuse
        # init_langfuse()

        context = subgraph.context
        path = subgraph.to_cypher_string(full_graph=False)

        group_chat, manager, user = create_group_chat()

        res = user.initiate_chat(
            manager,
            message=f"""Develop a research proposal using the following context:
Path: {path}

Context: {context}

Do not generate a new path. Use the provided path.

Do multiple iterations, like a feedback loop between a scientist and reviewers, to improve the research idea.

In the end, rate the novelty and feasibility of the research idea.""",
            clear_history=True,
        )
        messages = "\n".join([message["content"] for message in group_chat.messages])

        result = self.summarize_conversation(messages)
        references_obj = self.get_references(messages)

        return Hypothesis(
            title=result.title,
            statement=result.statement,
            source=subgraph,
            method=self,
            references=[
                f"Title: {reference.title} URL: {reference.url} Summary: {reference.summary}"
                for reference in references_obj.references
            ],
            metadata={"messages": res.chat_history},
        )

    def summarize_conversation(self, messages: str) -> HypgenResult:
        config = get_llm_config("large")
        client = OpenAIWrapper(
            config_list=config.config_list,
        )
        structured_res = client.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a summarizer of the conversation.",
                },
                {"role": "user", "content": messages},
            ],
            response_format=HypgenResult,
        )
        return HypgenResult.model_validate(
            json.loads(structured_res.choices[0].message.content)
        )

    def get_references(self, messages: str) -> ReferenceList:
        config = get_llm_config("large")
        client = OpenAIWrapper(
            config_list=config.config_list,
        )
        structured_res = client.create(
            messages=[
                {
                    "role": "system",
                    "content": "You gather the literature from the conversation",
                },
                {"role": "user", "content": messages},
            ],
            response_format=ReferenceList,
        )
        return ReferenceList.model_validate(
            json.loads(structured_res.choices[0].message.content)
        )

    def __str__(self) -> str:
        return "Autogen Hypothesis Generator"

    def to_json(self) -> dict[str, Any]:
        return {"type": "Autogen Hypothesis Generator"}
