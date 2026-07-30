from dataclasses import dataclass, field

from Bio.SeqRecord import SeqRecord

from .alignment import Alignment
from .containment import ContainmentMetrics


@dataclass(slots=True)
class ReferenceSequence:
    accession: str
    record: SeqRecord
    alignments: list[Alignment] = field(default_factory=list)
    containment: ContainmentMetrics = field(default_factory=ContainmentMetrics)

    @property
    def description(self):
        return self.record.description

    @property
    def sequence(self):
        return str(self.record.seq)

    @property
    def length(self):
        return len(self.record.seq)
