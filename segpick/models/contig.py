from dataclasses import dataclass, field

from Bio.SeqRecord import SeqRecord

from .alignment import Alignment
from .analysis import ContigAnalysis
from .metadata import ContigMetadata


@dataclass(slots=True)
class CandidateContig:
    """A candidate assembled contig for a BTV gene/segment."""

    id: str
    record: SeqRecord
    metadata: ContigMetadata
    analysis: ContigAnalysis = field(default_factory=ContigAnalysis)
    alignments: list[Alignment] = field(default_factory=list)

    @property
    def sequence(self) -> str:
        return str(self.record.seq)

    @property
    def length(self) -> int:
        return len(self.record.seq)

    @property
    def confidence(self) -> float:
        return self.metadata.confidence

    @property
    def z(self) -> float | None:
        return self.metadata.z

    @property
    def blast_reference(self) -> str | None:
        return self.metadata.sseqid
