from __future__ import annotations

import subprocess
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path

from segpick import __version__
from segpick.config import RunConfig
from segpick.models import AnalysisManifest, Sample
from segpick.reasoning.loader import RULE_SCHEMA_VERSION
from segpick.reasoning.rules import HypothesisRule
from segpick.scoring import GeneRecommendation


def _git_commit() -> str | None:
    package_root = Path(__file__).resolve().parents[2]
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=package_root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except OSError:
        return None
    commit = proc.stdout.strip()
    return commit if proc.returncode == 0 and commit else None


def build_analysis_manifest(
    sample: Sample,
    config: RunConfig,
    rules: Iterable[HypothesisRule],
    recommendations: Mapping[str, GeneRecommendation] | None = None,
) -> AnalysisManifest:
    """Build a reproducible run-level summary after analysis is complete."""

    active_rules = tuple(rules)
    sources = tuple(dict.fromkeys(rule.source for rule in active_rules))
    builtin_count = sum(rule.source.startswith("builtin:") for rule in active_rules)

    candidates = [
        candidate
        for gene in sample.genes.values()
        for candidate in gene.candidates
    ]
    observation_count = sum(len(candidate.analysis.observations) for candidate in candidates)
    candidate_finding_count = sum(len(candidate.analysis.findings) for candidate in candidates)
    gene_finding_count = sum(len(gene.findings) for gene in sample.genes.values())
    convergence_count = sum(len(candidate.analysis.convergences) for candidate in candidates)
    candidate_hypothesis_count = sum(len(candidate.analysis.hypotheses) for candidate in candidates)
    gene_hypothesis_count = sum(len(gene.hypotheses) for gene in sample.genes.values())

    recommendation_values = tuple((recommendations or {}).values())
    manual_review_count = sum(
        recommendation.report is not None and recommendation.report.manual_review
        for recommendation in recommendation_values
    )

    return AnalysisManifest(
        segpick_version=__version__,
        generated_utc=datetime.now(UTC).isoformat(),
        git_commit=_git_commit(),
        rule_schema_version=RULE_SCHEMA_VERSION,
        builtin_rule_count=builtin_count,
        user_rule_count=len(active_rules) - builtin_count,
        rule_sources=sources,
        gene_count=len(sample.genes),
        candidate_count=len(candidates),
        observation_count=observation_count,
        finding_count=candidate_finding_count + gene_finding_count,
        convergence_count=convergence_count,
        hypothesis_count=candidate_hypothesis_count + gene_hypothesis_count,
        recommended_gene_count=len(recommendation_values),
        manual_review_count=manual_review_count,
        resolved_config=config.to_dict(),
    )
