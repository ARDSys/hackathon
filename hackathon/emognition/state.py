from langgraph.graph import MessagesState


class HypgenState(MessagesState):
    subgraph: str
    mainstream_paths: str
    paths: str
    hypothesis: str


    literature: str
    references: list[str]

    hypothesis_1_text: str
    hypothesis_2_text: str
    hypothesis_3_text: str

    hypothesis_1_novelty: str
    hypothesis_2_novelty: str
    hypothesis_3_novelty: str

    hypothesis_1_impactfullness: str
    hypothesis_2_impactfullness: str
    hypothesis_3_impactfullness: str

    hypothesis_1_feasibility: str
    hypothesis_2_feasibility: str
    hypothesis_3_feasibility: str

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
