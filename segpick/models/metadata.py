from dataclasses import dataclass
@dataclass(slots=True)
class ContigMetadata:
    """Static metadata for a candidate contig from selected_hits.tsv."""
    segment: str
    score: float
    confidence: float
    cluster: str
    mean_length: float | None = None
    sd_length: float | None = None
    z: float | None = None
    qseqid: str | None = None
    sseqid: str | None = None
    pident: float | None = None
    alignment_len: float | None = None
    bitscore: float | None = None
    evalue: float | None = None
