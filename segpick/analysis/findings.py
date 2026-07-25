from __future__ import annotations

from segpick.analysis.protein_continuity import analyse_protein_continuity
from segpick.models import BiologicalFinding, CandidateContig, Gene, Sample


def candidate_biological_findings(
    candidate: CandidateContig,
) -> tuple[BiologicalFinding, ...]:
    """Create structured findings from existing candidate interpretations."""
    findings: list[BiologicalFinding] = []
    protein = candidate.analysis.protein_interpretation
    if protein is not None:
        if protein.possible_frameshift_pattern:
            findings.append(
                BiologicalFinding(
                    category="protein",
                    title="Possible frameshift pattern",
                    severity="review",
                    confidence="moderate",
                    scope="candidate",
                    summary=protein.summary,
                    sources=("protein_alignment",),
                    observation_types=tuple(
                        observation.observation_type
                        for observation in candidate.analysis.observations
                        if observation.source == "protein_alignment"
                    ),
                    candidate_ids=(candidate.id,),
                )
            )
        elif protein.structural_status == "intact":
            findings.append(
                BiologicalFinding(
                    category="protein",
                    title="Complete protein recovered",
                    severity="informational",
                    confidence="high",
                    scope="candidate",
                    summary=protein.summary,
                    sources=("protein_alignment",),
                    candidate_ids=(candidate.id,),
                )
            )
        elif protein.structural_status in {
            "truncated",
            "truncated_with_indels",
        }:
            findings.append(
                BiologicalFinding(
                    category="protein",
                    title="Protein truncation detected",
                    severity="warning",
                    confidence="high",
                    scope="candidate",
                    summary=protein.summary,
                    sources=("protein_alignment",),
                    observation_types=tuple(
                        observation.observation_type
                        for observation in candidate.analysis.observations
                        if observation.source == "protein_alignment"
                    ),
                    candidate_ids=(candidate.id,),
                )
            )
        else:
            findings.append(
                BiologicalFinding(
                    category="protein",
                    title="Internal protein differences",
                    severity="review",
                    confidence="moderate",
                    scope="candidate",
                    summary=protein.summary,
                    sources=("protein_alignment",),
                    observation_types=tuple(
                        observation.observation_type
                        for observation in candidate.analysis.observations
                        if observation.source == "protein_alignment"
                    ),
                    candidate_ids=(candidate.id,),
                )
            )

    relatedness = candidate.analysis.protein_relatedness
    if relatedness is not None:
        mapping = {
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
        title, severity, confidence = mapping.get(
            relatedness.classification,
            ("Protein relatedness finding", "review", "moderate"),
        )
        findings.append(
            BiologicalFinding(
                category="homology",
                title=title,
                severity=severity,
                confidence=confidence,
                scope="candidate",
                summary=relatedness.summary,
                sources=("diamond",),
                candidate_ids=(candidate.id,),
            )
        )

    return tuple(findings)


def gene_biological_findings(gene: Gene) -> tuple[BiologicalFinding, ...]:
    """Create gene-level findings from current assembly interpretations."""
    continuity = analyse_protein_continuity(gene)
    findings: list[BiologicalFinding] = []

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
                candidate_ids=tuple(
                    candidate.id for candidate in gene.candidates
                ),
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
                candidate_ids=tuple(
                    candidate.id for candidate in gene.candidates
                ),
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
                candidate_ids=tuple(
                    candidate.id for candidate in gene.candidates
                ),
            )
        )

    return tuple(findings)


def attach_biological_findings(sample: Sample) -> None:
    """Attach candidate- and gene-level findings after analyses are complete."""
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            candidate.analysis.findings = candidate_biological_findings(candidate)
        gene.findings = gene_biological_findings(gene)
