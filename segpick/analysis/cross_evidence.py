from __future__ import annotations

from collections.abc import Mapping

from segpick.analysis.evidence_assessments import build_evidence_assessments
from segpick.cross_evidence import CrossEvidenceContext, evaluate_cross_evidence
from segpick.models import BiologicalFinding, Sample
from segpick.scoring import GeneRecommendation


def attach_cross_evidence(sample: Sample, recommendations: Mapping[str, GeneRecommendation]) -> int:
    count = 0
    for gene in sample.genes.values():
        recommendation = recommendations.get(gene.name)
        if recommendation is None:
            continue
        by_id = {item.candidate_id: item for item in recommendation.candidates}
        for candidate in gene.candidates:
            ranked = by_id.get(candidate.id)
            if ranked is None:
                continue
            candidate.analysis.evidence_assessments = build_evidence_assessments(candidate, ranked)
            candidate.analysis.cross_evidence_findings = evaluate_cross_evidence(CrossEvidenceContext(candidate.analysis.evidence_assessments, candidate.id, gene.name))
            derived = tuple(
                BiologicalFinding(
                    category="cross_evidence",
                    title=item.title,
                    severity=item.severity,
                    confidence=item.confidence,
                    scope="candidate",
                    summary=item.description,
                    sources=("cross_evidence", item.source_plugin),
                    observation_types=(item.finding_id,),
                    candidate_ids=(candidate.id,),
                )
                for item in candidate.analysis.cross_evidence_findings
            )
            candidate.analysis.findings = (*candidate.analysis.findings, *derived)
            count += len(candidate.analysis.cross_evidence_findings)
    return count
