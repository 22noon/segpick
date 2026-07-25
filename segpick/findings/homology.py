from __future__ import annotations

from segpick.models import BiologicalFinding, CandidateContig


_RELATEDNESS_FINDINGS = {
    "well_supported_match": (
        "Well-supported protein match",
        "informational",
        "high",
    ),
    "well_supported_divergent_match": (
        "Divergent but structurally supported protein",
        "informational",
        "moderate",
    ),
    "partial_match": ("Partial protein match", "review", "moderate"),
    "ambiguous_assignment": (
        "Ambiguous protein assignment",
        "review",
        "moderate",
    ),
    "weak_or_unresolved_homology": (
        "Weak or unresolved protein homology",
        "warning",
        "low",
    ),
}


def generate_homology_findings(
    candidate: CandidateContig,
) -> tuple[BiologicalFinding, ...]:
    """Create candidate-level findings from protein relatedness."""
    relatedness = candidate.analysis.protein_relatedness
    if relatedness is None:
        return ()

    title, severity, confidence = _RELATEDNESS_FINDINGS.get(
        relatedness.classification,
        ("Protein relatedness finding", "review", "moderate"),
    )
    return (
        BiologicalFinding(
            category="homology",
            title=title,
            severity=severity,
            confidence=confidence,
            scope="candidate",
            summary=relatedness.summary,
            sources=("diamond",),
            candidate_ids=(candidate.id,),
        ),
    )
