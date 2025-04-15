from langgraph.graph import MessagesState
from typing_extensions import Literal


class HypgenState(MessagesState):
    subgraph: str
    context: str
    hypothesis: str

    novelty_loop_output: str

    literature: str
    references: list[str]

    novelty: str
    feasibility: str
    impact: str
    hot_topic_review: str
    # ethics_analysis: str

    critique: str
    summary: str
    title: str

    nice_reviewer_output: str
    rude_reviewer_output: str
    methodology_output: str
    methodology_review_summary_output: str

    iteration: int
    novelty_loop_iteration: int
    novelty_loop_decision: Literal["ACCEPT", "REJECT"]
