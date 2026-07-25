from __future__ import annotations

from segpick.models import BiologicalFinding, CandidateContig


def generate_convergence_findings(
    candidate: CandidateContig,
) -> tuple[BiologicalFinding, ...]:
    """Create candidate-level findings from spatial evidence convergence."""

    findings: list[BiologicalFinding] = []
    for convergence in candidate.analysis.convergences:
        findings.append(
            BiologicalFinding(
                category="convergence",
                title="Local evidence convergence",
                severity="review",
                confidence=(
                    "high"
                    if convergence.strength in {"strong", "very_strong"}
                    else "moderate"
                ),
                scope="candidate",
                summary=convergence.summary,
                sources=convergence.sources,
                observation_types=convergence.observation_types,
                candidate_ids=(candidate.id,),
            )
        )
    return tuple(findings)
