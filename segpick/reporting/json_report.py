from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from segpick.alignment.export import safe_name
from segpick.models import Sample
from segpick.scoring import GeneRecommendation


def write_gene_json_reports(
    sample: Sample,
    outdir: str | Path,
    recommendations: Mapping[str, GeneRecommendation] | None = None,
) -> None:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for name, g in sample.genes.items():
        payload = {
            "gene": g.name,
            "segment": g.segment,
            "anchor": g.anchor_id,
            "candidates": [],
            "references": [],
        }
        if recommendations and g.name in recommendations:
            payload["recommendation"] = recommendations[g.name].to_dict()
        else:
            payload["recommendation"] = None

        for c in g.candidates:
            payload["candidates"].append(
                {
                    "id": c.id,
                    "length": c.length,
                    "confidence": c.metadata.confidence,
                    "score": c.metadata.score,
                    "z": c.metadata.z,
                    "cluster": c.metadata.cluster,
                    "blast_reference": c.metadata.sseqid,
                    "blastx": (
                        c.analysis.blastx.to_dict()
                        if c.analysis.blastx is not None
                        else None
                    ),
                    "containment": c.analysis.containment.to_dict(),
                    "orf": (
                        c.analysis.orf.to_dict()
                        if c.analysis.orf is not None
                        else None
                    ),
                    "orf_alignment": (
                        c.analysis.orf_alignment.to_dict()
                        if c.analysis.orf_alignment is not None
                        else None
                    ),
                    "orf_quality": (
                        c.analysis.orf_quality.to_dict()
                        if c.analysis.orf_quality is not None
                        else None
                    ),
                }
            )
        for r in g.references:
            payload["references"].append(
                {
                    "id": r.accession,
                    "description": r.description,
                    "length": r.length,
                    "containment": r.containment.to_dict(),
                }
            )
        (outdir / f"{safe_name(name)}.json").write_text(json.dumps(payload, indent=2))
