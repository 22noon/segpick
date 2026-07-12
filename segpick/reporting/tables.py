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
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "gene",
        "segment",
        "sequence_id",
        "sequence_type",
        "is_anchor",
        "length",
        "confidence",
        "z",
        "cluster",
        "query_coverage",
        "anchor_coverage",
        "identity",
        "fragmentation",
        "n_blocks",
        "left_clip",
        "right_clip",
        "orientation",
        "structural_score",
        "status",
    ]
    with path.open("w") as h:
        h.write("\t".join(cols) + "\n")
        for name in sorted(sample.genes):
            g = sample.genes[name]
            for c in g.candidates:
                m = c.analysis.containment
                row = [
                    g.name,
                    g.segment,
                    c.id,
                    "candidate",
                    str(c.id == g.anchor_id),
                    str(c.length),
                    str(c.metadata.confidence),
                    "" if c.metadata.z is None else str(c.metadata.z),
                    c.metadata.cluster,
                    f"{m.query_coverage:.6f}",
                    f"{m.anchor_coverage:.6f}",
                    f"{m.identity:.6f}",
                    f"{m.fragmentation:.6f}",
                    str(m.n_blocks),
                    str(m.left_clip),
                    str(m.right_clip),
                    m.orientation,
                    f"{m.structural_score:.6f}",
                    m.status,
                ]
                h.write("\t".join(row) + "\n")
            for r in g.references:
                m = r.containment
                row = [
                    g.name,
                    g.segment,
                    r.accession,
                    "reference",
                    str(r.accession == g.anchor_id),
                    str(r.length),
                    "",
                    "",
                    "",
                    f"{m.query_coverage:.6f}",
                    f"{m.anchor_coverage:.6f}",
                    f"{m.identity:.6f}",
                    f"{m.fragmentation:.6f}",
                    str(m.n_blocks),
                    str(m.left_clip),
                    str(m.right_clip),
                    m.orientation,
                    f"{m.structural_score:.6f}",
                    m.status,
                ]
                h.write("\t".join(row) + "\n")
