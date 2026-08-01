from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from segpick.alignment.export import safe_name
from segpick.analysis import analyse_protein_continuity, build_evidence_assessments
from segpick.models import AnalysisManifest, Sample
from segpick.scoring import GeneRecommendation


def write_gene_json_reports(
    sample: Sample,
    outdir: str | Path,
    recommendations: Mapping[str, GeneRecommendation] | None = None,
    manifest: AnalysisManifest | None = None,
) -> None:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for name, g in sample.genes.items():
        payload = {
            "analysis_manifest": manifest.to_dict() if manifest is not None else None,
            "gene": g.name,
            "segment": g.segment,
            "anchor": g.anchor_id,
            "candidates": [],
            "references": [],
            "protein_continuity": analyse_protein_continuity(g).to_dict(),
            "biological_findings": [
                finding.to_dict() for finding in g.findings
            ],
            "biological_hypotheses": [hypothesis.to_dict() for hypothesis in g.hypotheses],
            "rule_evaluations": [item.to_dict() for item in g.rule_evaluations],
            "evidence_patterns": [item.to_dict() for item in g.evidence_patterns],
            "biological_hypothesis_evaluations": [item.to_dict() for item in g.biological_hypothesis_evaluations],
            "contig_dotplots": [item.to_dict() for item in g.contig_dotplots],
        }
        if recommendations and g.name in recommendations:
            payload["recommendation"] = recommendations[g.name].to_dict()
        else:
            payload["recommendation"] = None

        recommendation_by_id = {item.candidate_id: item for item in recommendations[g.name].candidates} if recommendations and g.name in recommendations else {}
        for c in g.candidates:
            candidate_recommendation = recommendation_by_id.get(c.id)
            payload["candidates"].append(
                {
                    "evidence_assessments": [item.to_dict() for item in c.analysis.evidence_assessments] if c.analysis.evidence_assessments else ([item.to_dict() for item in build_evidence_assessments(c, candidate_recommendation)] if candidate_recommendation is not None else []),
                    "cross_evidence_findings": [item.to_dict() for item in c.analysis.cross_evidence_findings],
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
                    "blastx_anchored_orf": (
                        c.analysis.blastx_anchored_orf.to_dict()
                        if c.analysis.blastx_anchored_orf is not None
                        else None
                    ),
                    "protein_relatedness": (
                        c.analysis.protein_relatedness.to_dict()
                        if c.analysis.protein_relatedness is not None
                        else None
                    ),
                    "structural_integrity": (c.analysis.structural_integrity.to_dict() if c.analysis.structural_integrity is not None else None),
                    "reference_compatibility": (c.analysis.reference_compatibility.to_dict() if c.analysis.reference_compatibility is not None else None),
                    "reference_dotplot": (
                        c.analysis.reference_dotplot.to_dict()
                        if c.analysis.reference_dotplot is not None
                        else None
                    ),
                    "boundary_coverage_assessments": [
                        item.to_dict() for item in c.analysis.boundary_coverage
                    ],
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
                    "biological_hypotheses": [hypothesis.to_dict() for hypothesis in c.analysis.hypotheses],
                    "rule_evaluations": [item.to_dict() for item in c.analysis.rule_evaluations],
                    "evidence_patterns": [item.to_dict() for item in c.analysis.evidence_patterns],
                    "biological_hypothesis_evaluations": [item.to_dict() for item in c.analysis.biological_hypothesis_evaluations],
                    "evidence_convergence": [
                        convergence.to_dict()
                        for convergence in c.analysis.convergences
                    ],
                    "observations": [
                        observation.to_dict()
                        for observation in c.analysis.observations
                    ],
                    "reasoning_graph": (
                        c.analysis.reasoning_graph.to_dict()
                        if c.analysis.reasoning_graph is not None
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
                }
            )
        (outdir / f"{safe_name(name)}.json").write_text(json.dumps(payload, indent=2))


def write_analysis_manifest(manifest: AnalysisManifest, path: str | Path) -> Path:
    """Write the run-level manifest as JSON."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest.to_dict(), indent=2))
    return path
