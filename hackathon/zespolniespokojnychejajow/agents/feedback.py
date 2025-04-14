from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role
from ..metrics_llm import fs_score, cs_score, ns_score, gp_score, nc_score
from ..lambda_utils import compute_lambda, build_prompt  # zakładam, że masz te funkcje


def create_feedback_loop_refiner_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a hypothesis feedback loop refiner agent using lambda control."""

    llm = get_model(model, **kwargs)

    def agent_with_feedback_loop(state: HypgenState, max_iterations: int = 1) -> HypgenState:
        logger.info("Running feedback loop agent")

        # Pobierz dane wejściowe
        hypothesis = state.get("hypothesis", "")
        subgraph_raw = state.get("subgraph", "")
        subgraph_texts = subgraph_raw.split("\n") if isinstance(subgraph_raw, str) else subgraph_raw
        lambda_val = state.get("lambda_val", 0.5)

        # Zbuduj prompt zależnie od lambda
        prompt_text = build_prompt(hypothesis, lambda_val, subgraph_texts)
        prompt = PromptTemplate.from_template(prompt_text)
        chain = prompt | llm

        # Wygeneruj nową hipotezę
        response = chain.invoke(state)
        content = response.content

        # Oblicz metryki + lambda ponownie (dla wygenerowanej wersji)
        try:
            metrics = {
                "FS": int(fs_score(content, state)),
                "CS": int(cs_score(content, state)),
                "NS": int(ns_score(content, state)),
                "GP": int(gp_score(content, state)),
                "NC": int(nc_score(content, state)),
                "LI": int(state.get("literature_integration_score", 5))  # fallback
            }

            lambda_val = compute_lambda(metrics)
            logger.info(f"[Feedback] Computed lambda: {lambda_val}")
        except Exception as e:
            logger.warning(f"[Feedback] Metric/lambda calc failed: {e}")
            metrics = {}
            lambda_val = 0.5

        return {
            "hypothesis": content,
            "messages": [add_role(response, "hypothesis_feedback_refiner")],
            "iteration": state.get("iteration", 0) + 1,
            "metrics": metrics,
            "lambda_val": lambda_val,
        }

    return {"agent": agent_with_feedback_loop}
