from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from Bio import SeqIO

from segpick.alignment.export import safe_name
from segpick.models import BlastNHSP, CandidateContig, Gene, ReferenceDotplot, Sample

OUTFMT_FIELDS = (
    "qseqid sseqid qlen slen pident length mismatch gapopen "
    "qstart qend sstart send evalue bitscore"
)


def reference_dotplot_filename(candidate_id: str, reference_id: str) -> str:
    return f"{safe_name(candidate_id)}__vs__{safe_name(reference_id)}.megablast.tsv"


def _covered_fraction(intervals: list[tuple[int, int]], length: int) -> float:
    if length <= 0 or not intervals:
        return 0.0
    merged: list[list[int]] = []
    for start, end in sorted((min(a, b), max(a, b)) for a, b in intervals):
        if not merged or start > merged[-1][1] + 1:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    covered = sum(end - start + 1 for start, end in merged)
    return min(1.0, covered / length)


def parse_megablast_tsv(
    path: str | Path,
    *,
    candidate_id: str,
    reference_id: str,
    query_length: int,
    reference_length: int,
    reused_existing: bool,
) -> ReferenceDotplot:
    path = Path(path)
    hsps: list[BlastNHSP] = []
    if path.exists():
        for line_number, raw in enumerate(path.read_text().splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) != 14:
                raise ValueError(
                    f"Expected 14 MegaBLAST columns in {path} line {line_number}; "
                    f"found {len(fields)}"
                )
            hsps.append(
                BlastNHSP(
                    query_id=fields[0],
                    subject_id=fields[1],
                    query_length=int(fields[2]),
                    subject_length=int(fields[3]),
                    percent_identity=float(fields[4]),
                    alignment_length=int(fields[5]),
                    mismatches=int(fields[6]),
                    gap_opens=int(fields[7]),
                    query_start=int(fields[8]),
                    query_end=int(fields[9]),
                    subject_start=int(fields[10]),
                    subject_end=int(fields[11]),
                    evalue=float(fields[12]),
                    bitscore=float(fields[13]),
                )
            )
    identities = [hsp.percent_identity for hsp in hsps]
    return ReferenceDotplot(
        candidate_id=candidate_id,
        reference_id=reference_id,
        query_length=query_length,
        reference_length=reference_length,
        hsps=tuple(hsps),
        query_coverage=_covered_fraction(
            [(hsp.query_start, hsp.query_end) for hsp in hsps], query_length
        ),
        reference_coverage=_covered_fraction(
            [(hsp.subject_start, hsp.subject_end) for hsp in hsps], reference_length
        ),
        identity_min=min(identities) if identities else None,
        identity_max=max(identities) if identities else None,
        output_path=str(path),
        reused_existing=reused_existing,
    )


def _reference_for_candidate(gene: Gene, candidate: CandidateContig):
    reference_id = candidate.blast_reference
    if reference_id is None:
        return None
    return next(
        (reference for reference in gene.references if reference.accession == reference_id),
        None,
    )


def run_candidate_megablast(
    candidate: CandidateContig,
    reference,
    outdir: str | Path,
    *,
    task: str = "megablast",
    evalue: float = 1e-5,
    word_size: int | None = None,
    force: bool = False,
) -> ReferenceDotplot:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    output = outdir / reference_dotplot_filename(candidate.id, reference.accession)
    complete_marker = output.with_suffix(output.suffix + ".complete")

    reused_existing = (
        output.exists()
        and (output.stat().st_size > 0 or complete_marker.exists())
        and not force
    )
    if not reused_existing:
        if shutil.which("blastn") is None:
            raise FileNotFoundError(
                "Reference dot plots requested, but blastn was not found on PATH. "
                "Install NCBI BLAST+ or disable reference dot plots."
            )
        with tempfile.TemporaryDirectory(prefix="segpick_megablast_") as tmp:
            tmpdir = Path(tmp)
            query_path = tmpdir / "query.fa"
            subject_path = tmpdir / "subject.fa"
            SeqIO.write([candidate.record], query_path, "fasta")
            SeqIO.write([reference.record], subject_path, "fasta")
            command = [
                "blastn",
                "-query", str(query_path),
                "-subject", str(subject_path),
                "-task", task,
                "-evalue", str(evalue),
                "-outfmt", f"6 {OUTFMT_FIELDS}",
                "-out", str(output),
            ]
            if word_size is not None:
                command.extend(["-word_size", str(word_size)])
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                output.unlink(missing_ok=True)
                complete_marker.unlink(missing_ok=True)
                message = result.stderr.strip() or result.stdout.strip()
                raise RuntimeError(
                    f"blastn failed for {candidate.id} versus {reference.accession}: {message}"
                )
            complete_marker.write_text("complete\n")

    return parse_megablast_tsv(
        output,
        candidate_id=candidate.id,
        reference_id=reference.accession,
        query_length=candidate.length,
        reference_length=reference.length,
        reused_existing=reused_existing,
    )


def attach_reference_dotplots(
    sample: Sample,
    outdir: str | Path,
    *,
    task: str = "megablast",
    evalue: float = 1e-5,
    word_size: int | None = None,
    force: bool = False,
    strict: bool = False,
) -> tuple[int, int]:
    attempted = 0
    attached = 0
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            reference = _reference_for_candidate(gene, candidate)
            if reference is None:
                if strict and candidate.blast_reference is not None:
                    raise KeyError(
                        f"Closest reference {candidate.blast_reference!r} for "
                        f"{candidate.id!r} is unavailable"
                    )
                continue
            attempted += 1
            candidate.analysis.reference_dotplot = run_candidate_megablast(
                candidate,
                reference,
                outdir,
                task=task,
                evalue=evalue,
                word_size=word_size,
                force=force,
            )
            attached += 1
    return attached, attempted
