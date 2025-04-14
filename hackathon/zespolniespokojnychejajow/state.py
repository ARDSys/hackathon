from langgraph.graph import MessagesState


class HypgenState(MessagesState):
    # Required fields
    subgraph: str
    context: str
    hypothesis: str
    critique: str
    
    # Optional fields that are initialized with defaults
    title: str = ""
    iteration: int = 0
    
    # Fields included for backward compatibility with metadata
    summary: str = ""
    novelty: str = ""
    feasibility: str = ""
    impact: str = ""
    literature: str = ""
    references: list = []
