from dataclasses import dataclass, field

from Bio.SeqRecord import SeqRecord

from .alignment import Alignment
from .contig import CandidateContig
from .contig_dotplot import ContigDotplot
from .finding import BiologicalFinding
from .hypothesis import BiologicalHypothesis
from .reference import ReferenceSequence
from .rule_evaluation import RuleEvaluation


@dataclass(slots=True)
class Gene:
    """A BTV gene/segment as the basic unit of analysis."""

    name: str
    segment: str
    candidates: list[CandidateContig] = field(default_factory=list)
    references: list[ReferenceSequence] = field(default_factory=list)
    alignments: list[Alignment] = field(default_factory=list)
    anchor_id: str | None = None
    recommendation: CandidateContig | None = None
    findings: tuple[BiologicalFinding, ...] = ()
    hypotheses: tuple[BiologicalHypothesis, ...] = ()
    rule_evaluations: tuple[RuleEvaluation, ...] = ()
    contig_dotplots: tuple[ContigDotplot, ...] = ()

    def add_candidate(self, contig: CandidateContig) -> None:
        self.candidates.append(contig)

    def add_reference(self, reference: ReferenceSequence) -> None:
        if reference.accession not in {r.accession for r in self.references}:
            self.references.append(reference)

    def all_records(self) -> list[SeqRecord]:
        return [c.record for c in self.candidates] + [r.record for r in self.references]

    def longest_sequence_id(self) -> str | None:
        records = [(c.id, c.length) for c in self.candidates] + [(r.accession, r.length) for r in self.references]
        return None if not records else max(records, key=lambda x: x[1])[0]

    def anchor_record(self) -> SeqRecord | None:
        anchor = self.anchor_id or self.longest_sequence_id()
        if anchor is None:
            return None
        for c in self.candidates:
            if c.id == anchor:
                return c.record
        for r in self.references:
            if r.accession == anchor:
                return r.record
        return None

    def best_by_confidence(self) -> CandidateContig | None:
        return None if not self.candidates else max(self.candidates, key=lambda c: c.confidence)

    def attach_alignments(self, alignments: list[Alignment]) -> None:
        self.alignments = alignments
        by_id = {c.id: c for c in self.candidates}
        by_id.update({r.accession: r for r in self.references})
        for aln in alignments:
            obj = by_id.get(aln.query_id)
            if obj is not None:
                obj.alignments.append(aln)

    def summary_dict(self) -> dict[str, object]:
        best = self.best_by_confidence()
        return {
            "gene": self.name,
            "segment": self.segment,
            "n_candidates": len(self.candidates),
            "n_references": len(self.references),
            "n_alignments": len(self.alignments),
            "anchor": self.anchor_id or self.longest_sequence_id(),
            "best_by_confidence": best.id if best else None,
        }
