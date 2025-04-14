from langgraph.graph import MessagesState


class HypgenState(MessagesState):
    subgraph: str
    paths: str
    hypothesis: str

    literature: str
    references: list[str]

    novelty: str
    feasibility: str
    impact: str

    reviewer_1_profile: str
    reviewer_2_profile: str
    reviewer_3_profile: str

    review_1: str
    review_2: str
    review_3: str

    critique: str
    summary: str
    title: str

    iteration: int
