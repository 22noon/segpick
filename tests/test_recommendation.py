from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.models import CandidateContig, ContigMetadata


def candidate(name, confidence, status, structural):
    c = CandidateContig(
        id=name,
        record=SeqRecord(Seq("A" * 100), id=name),
        metadata=ContigMetadata(segment="2", score=1, confidence=confidence, cluster="x"),
    )
    c.analysis.containment.status = status
    c.analysis.containment.structural_score = structural
    c.analysis.containment.identity = 0.99
    c.analysis.containment.query_coverage = 1.0
    return c
