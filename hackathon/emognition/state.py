from langgraph.graph import MessagesState


class HypgenState(MessagesState):
    subgraph: str
    mainstream_paths: str
    paths: str
    hypothesis: str


    literature: str
    references: list[str]

    novelty: str
    feasibility: str
    impact: str

    selected_hypotheses: str

    hypothesis_1_reviewer_1_profile: str
    hypothesis_1_reviewer_2_profile: str
    hypothesis_1_reviewer_3_profile: str

    hypothesis_2_reviewer_1_profile: str
    hypothesis_2_reviewer_2_profile: str
    hypothesis_2_reviewer_3_profile: str

    hypothesis_3_reviewer_1_profile: str
    hypothesis_3_reviewer_2_profile: str
    hypothesis_3_reviewer_3_profile: str

    hypothesis_1_review_1: str
    hypothesis_1_review_2: str
    hypothesis_1_review_3: str

    hypothesis_2_review_1: str
    hypothesis_2_review_2: str
    hypothesis_2_review_3: str

    hypothesis_3_review_1: str
    hypothesis_3_review_2: str
    hypothesis_3_review_3: str

    critique_1: str
    critique_2: str
    critique_3: str

    summary: str
    title: str

    iteration: int
