from dataclasses import dataclass
from .enums import ScientificQuestionType

@dataclass(frozen=True)
class ScientificQuestion:
    question_type: ScientificQuestionType
    subject:str
    text:str

@dataclass(frozen=True)
class ScientificConclusion:
    result:str
    summary:str

@dataclass(frozen=True)
class ReasoningPath:
    node_ids: tuple[str,...]=()

@dataclass(frozen=True)
class Argument:
    claim:str
    status:str
    reasoning_path:ReasoningPath
    supporting_nodes: tuple[str,...]=()
    contradicting_nodes: tuple[str,...]=()
    missing_nodes: tuple[str,...]=()

@dataclass(frozen=True)
class ScientificJustification:
    primary_argument:Argument
    competing_arguments: tuple[Argument,...]=()

@dataclass(frozen=True)
class Provenance:
    graph_version:str=''
    knowledge_version:str=''

@dataclass(frozen=True)
class ScientificArgument:
    question:ScientificQuestion
    conclusion:ScientificConclusion
    justification:ScientificJustification
    provenance:Provenance
