from langgraph.graph import MessagesState


class HypgenState(MessagesState):
    subgraph: str
    context: str
    hypothesis: str

    literature: str
    references: list[str]

    novelty_and_impact_score: str
    feasibility_score: str
    
    experiment_plan: str
    feasibility_description: str
    novelty_and_impact_description: str

    critique: str
    summary: str
    title: str

    iteration: int
