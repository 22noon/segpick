from pathlib import Path


def write_summary_tsv(sample, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as h:
        h.write("gene\tsegment\tn_candidates\tn_references\tn_alignments\tanchor\tbest_by_confidence\n")
        for name in sorted(sample.genes):
            r = sample.genes[name].summary_dict()
            h.write(f"{r['gene']}\t{r['segment']}\t{r['n_candidates']}\t{r['n_references']}\t{r['n_alignments']}\t{r['anchor']}\t{r['best_by_confidence']}\n")


def write_metrics_tsv(sample, path):
    """Write MegaBLAST-derived reference structural integrity metrics."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "gene", "segment", "candidate", "reference", "length",
        "candidate_coverage", "reference_coverage", "block_count",
        "longest_block_fraction", "largest_candidate_gap",
        "largest_reference_gap", "continuity", "orientation_consistency",
        "order_consistency", "structural_integrity", "status",
    ]
    with path.open("w") as handle:
        handle.write("\t".join(cols) + "\n")
        for name in sorted(sample.genes):
            gene = sample.genes[name]
            for candidate in gene.candidates:
                m = candidate.analysis.structural_integrity
                if m is None:
                    row = [gene.name, gene.segment, candidate.id, candidate.blast_reference or "", str(candidate.length)] + [""] * 11
                else:
                    row = [
                        gene.name, gene.segment, candidate.id, m.reference_id, str(candidate.length),
                        f"{m.candidate_coverage:.6f}", f"{m.reference_coverage:.6f}", str(m.block_count),
                        f"{m.longest_block_fraction:.6f}", str(m.largest_candidate_gap), str(m.largest_reference_gap),
                        f"{m.continuity:.6f}", f"{m.orientation_consistency:.6f}",
                        f"{m.order_consistency:.6f}", f"{m.score:.6f}", m.status,
                    ]
                handle.write("\t".join(row) + "\n")

