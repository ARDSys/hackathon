import json
from typing import Any, Dict, Literal, Optional
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from langchain_core.messages import AIMessage
from loguru import logger

from ..state import HackathonState
from ..llm.utils import get_model


class CriticOutput(BaseModel):
    critique: str
    is_accepted: bool


CRITIC_PROMPT = """
You are a biomedical research critic tasked with evaluating research hypotheses.

Given a hypothesis and the underlying mechanistic summaries, evaluate whether the hypothesis is:
1. Novel - provides new insights or connections not obvious from existing literature
2. Correct - logically follows from the provided mechanistic evidence
3. Valuable - has potential significance in the biomedical field

Your task:
- Critically analyze the hypothesis
- Judge if it passes all criteria
- Provide clear reasoning for your decision

Return only valid JSON in the following format:
{{
  "critique": "<Detailed critique explaining your reasoning>",
  "is_accepted": <true if hypothesis is novel, correct, and valuable; false otherwise>
}}

Hypothesis Title: {title}
Hypothesis Statement: {statement}
Mechanistic Summaries: {mechanistic_summaries}
"""


def create_critic_analyst_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Creates a Critic Analyst Agent."""

    llm = get_model(model, **kwargs).with_structured_output(CriticOutput)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a biomedical hypothesis critic."),
        ("human", CRITIC_PROMPT)
    ])

    chain = prompt | llm

    def agent(state: HackathonState) -> HackathonState:
        logger.info("🔍 Evaluating hypothesis quality and novelty")

        try:
            summaries = json.dumps(state.get("mechanistic_summaries", []), indent=2)
            result: CriticOutput = chain.invoke({
                "title": state.get("title", ""),
                "statement": state.get("statement", ""),
                "mechanistic_summaries": summaries
            })

            status = "ACCEPT" if result.is_accepted else "REJECT"
            logger.info(f"📝 Critique completed: {status}")
            
            # Increment iteration if rejected
            iteration = state.get("iteration", 0)
            if not result.is_accepted:
                iteration += 1
            
            return {
                "critique": f"{status}: {result.critique}",
                "iteration": iteration,
                "messages": state.get("messages", []) + [
                    AIMessage(name="critic_analyst", content=f"Critique: {result.critique}\nDecision: {status}")
                ],
            }

        except Exception as e:
            logger.warning(f"❌ Failed to generate critique: {e}")
            return {
                "critique": "REJECT: Failed to properly evaluate the hypothesis.",
                "iteration": state.get("iteration", 0) + 1,  # Increment iteration on error
                "messages": state.get("messages", []) + [
                    AIMessage(name="critic_analyst", content="Failed to evaluate hypothesis.")
                ],
            }

    return {"agent": agent} 