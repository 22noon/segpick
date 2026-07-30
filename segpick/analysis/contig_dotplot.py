from __future__ import annotations

import shutil
import subprocess
import tempfile
from itertools import combinations
from pathlib import Path

from Bio import SeqIO

from segpick.alignment.export import safe_name
from segpick.analysis.reference_dotplot import OUTFMT_FIELDS, _covered_fraction
from segpick.models import BlastNHSP, CandidateContig, ContigDotplot, Gene, Sample


def canonical_contig_pair(first_id: str, second_id: str) -> tuple[str, str]:
    return tuple(sorted((first_id, second_id)))


def contig_dotplot_filename(first_id: str, second_id: str) -> str:
    left, right = canonical_contig_pair(first_id, second_id)
    return f"{safe_name(left)}__vs__{safe_name(right)}.megablast.tsv"


def parse_contig_megablast_tsv(
    path: str | Path,
    *,
    query_id: str,
    target_id: str,
    query_length: int,
    target_length: int,
    reused_existing: bool,
) -> ContigDotplot:
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
    return ContigDotplot(
        query_id=query_id,
        target_id=target_id,
        query_length=query_length,
        target_length=target_length,
        hsps=tuple(hsps),
        query_coverage=_covered_fraction(
            [(hsp.query_start, hsp.query_end) for hsp in hsps], query_length
        ),
        target_coverage=_covered_fraction(
            [(hsp.subject_start, hsp.subject_end) for hsp in hsps], target_length
        ),
        identity_min=min(identities) if identities else None,
        identity_max=max(identities) if identities else None,
        output_path=str(path),
        reused_existing=reused_existing,
    )


def run_contig_pair_megablast(
    first: CandidateContig,
    second: CandidateContig,
    outdir: str | Path,
    *,
    task: str = "megablast",
    evalue: float = 1e-5,
    word_size: int | None = None,
    force: bool = False,
) -> ContigDotplot:
    left_id, right_id = canonical_contig_pair(first.id, second.id)
    by_id = {first.id: first, second.id: second}
    query = by_id[left_id]
    target = by_id[right_id]

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    output = outdir / contig_dotplot_filename(query.id, target.id)
    complete_marker = output.with_suffix(output.suffix + ".complete")
    reused_existing = (
        output.exists()
        and (output.stat().st_size > 0 or complete_marker.exists())
        and not force
    )
    if not reused_existing:
        if shutil.which("blastn") is None:
            raise FileNotFoundError(
                "Contig dot plots requested, but blastn was not found on PATH. "
                "Install NCBI BLAST+ or disable contig dot plots."
            )
        with tempfile.TemporaryDirectory(prefix="segpick_contig_megablast_") as tmp:
            tmpdir = Path(tmp)
            query_path = tmpdir / "query.fa"
            subject_path = tmpdir / "subject.fa"
            SeqIO.write([query.record], query_path, "fasta")
            SeqIO.write([target.record], subject_path, "fasta")
            command = [
                "blastn", "-query", str(query_path), "-subject", str(subject_path),
                "-task", task, "-evalue", str(evalue),
                "-outfmt", f"6 {OUTFMT_FIELDS}", "-out", str(output),
            ]
            if word_size is not None:
                command.extend(["-word_size", str(word_size)])
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                output.unlink(missing_ok=True)
                complete_marker.unlink(missing_ok=True)
                message = result.stderr.strip() or result.stdout.strip()
                raise RuntimeError(
                    f"blastn failed for {query.id} versus {target.id}: {message}"
                )
            complete_marker.write_text("complete\n")
    return parse_contig_megablast_tsv(
        output,
        query_id=query.id,
        target_id=target.id,
        query_length=query.length,
        target_length=target.length,
        reused_existing=reused_existing,
    )


def attach_contig_dotplots(
    sample: Sample,
    outdir: str | Path,
    *,
    task: str = "megablast",
    evalue: float = 1e-5,
    word_size: int | None = None,
    force: bool = False,
) -> tuple[int, int]:
    attempted = 0
    attached = 0
    for gene in sample.genes.values():
        results: list[ContigDotplot] = []
        for first, second in combinations(gene.candidates, 2):
            attempted += 1
            results.append(
                run_contig_pair_megablast(
                    first, second, outdir,
                    task=task,
                    evalue=evalue,
                    word_size=word_size,
                    force=force,
                )
            )
            attached += 1
        gene.contig_dotplots = tuple(results)
    return attached, attempted
