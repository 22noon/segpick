from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from segpick.alignment.export import safe_name
from segpick.analysis import analyse_protein_continuity
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
            "protein_continuity": analyse_protein_continuity(g).to_dict(),
            "biological_findings": [
                finding.to_dict() for finding in g.findings
            ],
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
                    "blastx_consistency": (
                        c.analysis.blastx_consistency.to_dict()
                        if c.analysis.blastx_consistency is not None
                        else None
                    ),
                    "protein_relatedness": (
                        c.analysis.protein_relatedness.to_dict()
                        if c.analysis.protein_relatedness is not None
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
                    "protein_interpretation": (
                        c.analysis.protein_interpretation.to_dict()
                        if c.analysis.protein_interpretation is not None
                        else None
                    ),
                    "biological_findings": [
                        finding.to_dict() for finding in c.analysis.findings
                    ],
                    "observations": [
                        observation.to_dict()
                        for observation in c.analysis.observations
                    ],
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
