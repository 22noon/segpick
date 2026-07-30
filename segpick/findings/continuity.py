from __future__ import annotations

from segpick.analysis.protein_continuity import analyse_protein_continuity
from segpick.models import BiologicalFinding, Gene


def generate_continuity_findings(gene: Gene) -> tuple[BiologicalFinding, ...]:
    """Create gene-level findings from protein continuity analysis."""
    continuity = analyse_protein_continuity(gene)
    findings: list[BiologicalFinding] = []
    all_candidate_ids = tuple(candidate.id for candidate in gene.candidates)

    if continuity.classification == "complete_single_candidate":
        findings.append(
            BiologicalFinding(
                category="assembly",
                title="Single-contig protein recovery",
                severity="informational",
                confidence="high",
                scope="gene",
                summary=continuity.summary,
                sources=("protein_continuity",),
                candidate_ids=all_candidate_ids,
            )
        )
    elif continuity.classification == "complementary_fragments":
        findings.append(
            BiologicalFinding(
                category="assembly",
                title="Possible split assembly",
                severity="warning",
                confidence="high",
                scope="gene",
                summary=continuity.summary,
                sources=("protein_continuity",),
                candidate_ids=continuity.complementary_candidate_ids,
            )
        )
    elif continuity.classification == "incomplete_recovery":
        findings.append(
            BiologicalFinding(
                category="assembly",
                title="Incomplete protein recovery",
                severity="warning",
                confidence="high",
                scope="gene",
                summary=continuity.summary,
                sources=("protein_continuity",),
                candidate_ids=all_candidate_ids,
            )
        )

    if continuity.redundant_overlap:
        findings.append(
            BiologicalFinding(
                category="assembly",
                title="Redundant overlapping protein fragments",
                severity="review",
                confidence="moderate",
                scope="gene",
                summary=(
                    "Multiple candidates cover substantially overlapping "
                    "protein regions; review for redundant or alternative "
                    "assemblies."
                ),
                sources=("protein_continuity",),
                candidate_ids=all_candidate_ids,
            )
        )

    return tuple(findings)
