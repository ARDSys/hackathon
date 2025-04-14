from langgraph.graph import MessagesState


class HypgenState(MessagesState):
    subgraph: str
    context: str
    hypothesis: str

    literature: str
    references: list[str]

    novelty: str
    feasibility: str
    impact: str

    critique: str
    summary: str
    title: str

    iteration: int
