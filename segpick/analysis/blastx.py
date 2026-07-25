from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from segpick.io.fasta import read_fasta_dict
from segpick.models import BlastXHit, Sample

BLASTX_FIELDS = (
    "qseqid",
    "sseqid",
    "stitle",
    "pident",
    "length",
    "evalue",
    "bitscore",
    "qstart",
    "qend",
    "sstart",
    "send",
    "qlen",
    "slen",
    "qframe",
)


@dataclass(frozen=True, slots=True)
class BlastXAttachmentSummary:
    candidate_count: int
    hits_attached: int
    subjects_resolved: int


def read_diamond_blastx(path: str | Path) -> dict[str, tuple[BlastXHit, ...]]:
    """Read headerless DIAMOND outfmt 6 output in SegPick's documented order."""

    grouped: dict[str, list[BlastXHit]] = {}
    with Path(path).open(newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for line_number, row in enumerate(reader, start=1):
            if not row:
                continue
            if len(row) != len(BLASTX_FIELDS):
                raise ValueError(
                    f"{path}:{line_number}: expected {len(BLASTX_FIELDS)} fields, "
                    f"found {len(row)}"
                )
            try:
                hit = BlastXHit(
                    query_id=row[0],
                    subject_id=row[1],
                    subject_title=row[2],
                    percent_identity=float(row[3]),
                    alignment_length=int(row[4]),
                    evalue=float(row[5]),
                    bitscore=float(row[6]),
                    query_start=int(row[7]),
                    query_end=int(row[8]),
                    subject_start=int(row[9]),
                    subject_end=int(row[10]),
                    query_length=int(row[11]),
                    subject_length=int(row[12]),
                    query_frame=int(row[13]),
                )
            except ValueError as exc:
                raise ValueError(f"{path}:{line_number}: invalid BLASTX value") from exc
            if hit.query_frame not in {-3, -2, -1, 1, 2, 3}:
                raise ValueError(
                    f"{path}:{line_number}: qframe must be one of -3,-2,-1,1,2,3"
                )
            grouped.setdefault(hit.query_id, []).append(hit)

    return {
        query_id: tuple(
            sorted(hits, key=lambda hit: (-hit.bitscore, hit.evalue, hit.subject_id))
        )
        for query_id, hits in grouped.items()
    }


def attach_blastx_hits(
    sample: Sample,
    blastx_path: str | Path,
    protein_fasta: str | Path,
    *,
    strict: bool = False,
) -> BlastXAttachmentSummary:
    """Attach the highest-bitscore DIAMOND hit and its subject protein."""

    hits_by_query = read_diamond_blastx(blastx_path)
    proteins = read_fasta_dict(protein_fasta)
    candidate_count = 0
    hits_attached = 0
    subjects_resolved = 0

    for gene in sample.genes.values():
        for candidate in gene.candidates:
            candidate_count += 1
            hits = hits_by_query.get(candidate.id)
            if not hits:
                if strict:
                    raise KeyError(f"No BLASTX hit found for candidate {candidate.id!r}")
                continue
            hit = hits[0]
            protein = proteins.get(hit.subject_id)
            if protein is None:
                if strict:
                    raise KeyError(
                        f"BLASTX subject {hit.subject_id!r} not found in {protein_fasta}"
                    )
            else:
                hit.subject_protein = str(protein.seq)
                subjects_resolved += 1
            candidate.analysis.blastx = hit
            hits_attached += 1

    return BlastXAttachmentSummary(
        candidate_count=candidate_count,
        hits_attached=hits_attached,
        subjects_resolved=subjects_resolved,
    )
