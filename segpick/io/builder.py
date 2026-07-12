from __future__ import annotations
from pathlib import Path
import math
import pandas as pd
from segpick.models import Sample, Gene, CandidateContig, ReferenceSequence, ContigMetadata
from .fasta import read_fasta_dict
from .hits import read_hits
def _optional_float(row: pd.Series, key: str) -> float | None:
    if key not in row or pd.isna(row[key]): return None
    try: value = float(row[key])
    except (TypeError, ValueError): return None
    return None if math.isnan(value) else value
def _metadata_from_row(row: pd.Series) -> ContigMetadata:
    return ContigMetadata(segment=str(row["segment"]), score=float(row["score"]), confidence=float(row["confidence"]), cluster=str(row["cluster"]), mean_length=_optional_float(row, "mean_length"), sd_length=_optional_float(row, "sd_length"), z=_optional_float(row, "z"), qseqid=str(row["qseqid"]) if "qseqid" in row and not pd.isna(row["qseqid"]) else None, sseqid=str(row["sseqid"]) if "sseqid" in row and not pd.isna(row["sseqid"]) else None, pident=_optional_float(row, "pident"), alignment_len=_optional_float(row, "len"), bitscore=_optional_float(row, "bitscore"), evalue=_optional_float(row, "evalue"))
def build_sample(hits_path: str | Path, contigs_fasta: str | Path, references_fasta: str | Path, sample_name: str = "sample", strict: bool = False) -> Sample:
    """Build a Sample object from selected hits, contigs, and references."""
    hits = read_hits(hits_path); contigs = read_fasta_dict(contigs_fasta); references = read_fasta_dict(references_fasta); sample = Sample(name=sample_name)
    for gene_name, group in hits.groupby("genes", sort=False):
        gene = Gene(name=str(gene_name), segment=str(group["segment"].iloc[0]))
        for _, row in group.iterrows():
            contig_id = str(row["contig"])
            if contig_id not in contigs:
                if strict: raise KeyError(f"Contig {contig_id!r} not found in {contigs_fasta}")
                continue
            metadata = _metadata_from_row(row); gene.add_candidate(CandidateContig(id=contig_id, record=contigs[contig_id], metadata=metadata))
            ref_id = metadata.sseqid
            if ref_id:
                if ref_id in references: gene.add_reference(ReferenceSequence(accession=ref_id, record=references[ref_id]))
                elif strict: raise KeyError(f"Reference {ref_id!r} not found in {references_fasta}")
        gene.anchor_id = gene.longest_sequence_id(); sample.add_gene(gene)
    return sample
