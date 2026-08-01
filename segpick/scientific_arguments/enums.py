from enum import Enum, auto
class ScientificQuestionType(Enum):
    EXPLAIN_RECOMMENDATION=auto()
    EXPLAIN_HYPOTHESIS=auto()
    COMPARE_CANDIDATES=auto()
    NEXT_EVIDENCE=auto()
    IMPACT_ANALYSIS=auto()
