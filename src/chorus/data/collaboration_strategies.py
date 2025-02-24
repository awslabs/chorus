from enum import StrEnum


class DecisionMakingStrategy(StrEnum):
    NONE = "none"
    FIRST_COME_FIRST_SERVE = "first_come_first_serve"
    MAJORITY_VOTE = "majority_vote"
    PLURALITY_VOTE = "plurality_vote"