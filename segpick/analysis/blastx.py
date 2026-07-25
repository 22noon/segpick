from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from segpick.io.fasta import read_fasta_dict
from segpick.models import BlastXHit, ProteinRelatedness, Sample

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


def _normalise_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _hit_matches_gene(hit: BlastXHit, gene_name: str) -> bool | None:
    gene_label = _normalise_label(gene_name)
    if not gene_label:
        return None
    subject_label = _normalise_label(f"{hit.subject_id} {hit.subject_title}")
    return gene_label in subject_label


def calculate_protein_relatedness(
    hits: tuple[BlastXHit, ...],
    gene_name: str,
    *,
    top_n: int = 10,
) -> ProteinRelatedness:
    """Summarise protein relatedness without treating divergence as poor assembly."""

    best = hits[0]
    top_hits = hits[:top_n]
    gene_calls = [_hit_matches_gene(hit, gene_name) for hit in top_hits]
    known_calls = [call for call in gene_calls if call is not None]
    agreement = (
        sum(call is True for call in known_calls) / len(known_calls)
        if known_calls
        else None
    )
    expected_gene_agrees = _hit_matches_gene(best, gene_name)

    assignment_ambiguous = (
        expected_gene_agrees is False
        or (agreement is not None and agreement < 0.60)
    )
    broad_coverage = best.subject_coverage >= 0.80 and best.query_coverage >= 0.50
    partial = best.subject_coverage < 0.70 or best.query_coverage < 0.40

    if assignment_ambiguous:
        classification = "ambiguous_assignment"
        summary = (
            "Top protein hits do not consistently support the expected gene "
            "assignment; manual review is recommended."
        )
    elif partial:
        classification = "partial_match"
        summary = (
            "Protein homology is limited to part of the candidate or reference "
            "protein; inspect ORF completeness and the alignment."
        )
    elif broad_coverage and best.percent_identity < 50.0:
        classification = "well_supported_divergent_match"
        summary = (
            "A broad, gene-consistent protein match is present despite low amino-"
            "acid identity, which may indicate a divergent lineage or limited "
            "database representation."
        )
    elif broad_coverage:
        classification = "well_supported_match"
        summary = (
            "The candidate has broad protein coverage and a consistent expected-"
            "gene assignment."
        )
    else:
        classification = "weak_or_unresolved_homology"
        summary = (
            "Protein homology is detected but does not yet provide broad, "
            "unambiguous support for the expected protein."
        )

    return ProteinRelatedness(
        subject_id=best.subject_id,
        subject_title=best.subject_title,
        percent_identity=best.percent_identity,
        query_coverage=best.query_coverage,
        subject_coverage=best.subject_coverage,
        bitscore=best.bitscore,
        evalue=best.evalue,
        expected_gene_agrees=expected_gene_agrees,
        top_hit_count=len(top_hits),
        top_hit_gene_agreement=agreement,
        classification=classification,
        summary=summary,
    )


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
            candidate.analysis.protein_relatedness = calculate_protein_relatedness(
                hits, gene.name
            )
            hits_attached += 1

    return BlastXAttachmentSummary(
        candidate_count=candidate_count,
        hits_attached=hits_attached,
        subjects_resolved=subjects_resolved,
    )
