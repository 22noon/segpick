from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AnalysisManifest:
    """Run-level provenance and reasoning metadata for a SegPick analysis."""

    segpick_version: str
    generated_utc: str
    git_commit: str | None
    rule_schema_version: int
    builtin_rule_count: int
    user_rule_count: int
    rule_sources: tuple[str, ...]
    gene_count: int
    candidate_count: int
    observation_count: int
    finding_count: int
    convergence_count: int
    hypothesis_count: int
    recommended_gene_count: int
    manual_review_count: int
    resolved_config: dict[str, Any]

    @property
    def total_rule_count(self) -> int:
        return self.builtin_rule_count + self.user_rule_count

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["rule_sources"] = list(self.rule_sources)
        payload["total_rule_count"] = self.total_rule_count
        return payload
