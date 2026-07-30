from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    channel_id: str
    finding_id: str
    title: str

    def to_dict(self) -> dict[str, str]:
        return {"channel_id": self.channel_id, "finding_id": self.finding_id, "title": self.title}


@dataclass(frozen=True, slots=True)
class EvidenceContribution:
    """One traceable contribution to a cross-evidence inference."""

    role: str
    channel_id: str
    finding_id: str
    title: str
    weight: float = 1.0
    confidence: float | None = None
    present: bool = True
    explanation: str = ""

    @property
    def reference(self) -> EvidenceReference:
        return EvidenceReference(self.channel_id, self.finding_id, self.title)

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "channel_id": self.channel_id,
            "finding_id": self.finding_id,
            "title": self.title,
            "weight": self.weight,
            "confidence": self.confidence,
            "present": self.present,
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class CrossEvidenceFinding:
    finding_id: str
    title: str
    description: str
    confidence: str
    severity: str
    priority: int
    rule_id: str
    rule_version: str
    source_plugin: str = "segpick.core"
    supporting_evidence: tuple[EvidenceReference, ...] = ()
    conflicting_evidence: tuple[EvidenceReference, ...] = ()
    limitations: tuple[str, ...] = ()
    participates_in_ranking: bool = False
    support_contributions: tuple[EvidenceContribution, ...] = ()
    contradiction_contributions: tuple[EvidenceContribution, ...] = ()
    missing_contributions: tuple[EvidenceContribution, ...] = ()
    confidence_score: float | None = None
    confidence_method: str = "legacy_rule_confidence"
    confidence_method_version: str = "1.0"
    evidence_completeness: float | None = None
    match_status: str = "complete"

    def __post_init__(self) -> None:
        # Preserve the v1 reference interface for reasoners using structured
        # contributions, and preserve structured output for legacy plug-ins.
        if self.support_contributions and not self.supporting_evidence:
            object.__setattr__(self, "supporting_evidence", tuple(item.reference for item in self.support_contributions if item.present))
        if self.contradiction_contributions and not self.conflicting_evidence:
            object.__setattr__(self, "conflicting_evidence", tuple(item.reference for item in self.contradiction_contributions if item.present))
        if self.supporting_evidence and not self.support_contributions:
            object.__setattr__(self, "support_contributions", tuple(
                EvidenceContribution("support", item.channel_id, item.finding_id, item.title)
                for item in self.supporting_evidence
            ))
        if self.conflicting_evidence and not self.contradiction_contributions:
            object.__setattr__(self, "contradiction_contributions", tuple(
                EvidenceContribution("contradiction", item.channel_id, item.finding_id, item.title)
                for item in self.conflicting_evidence
            ))

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.finding_id,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence,
            "confidence_score": self.confidence_score,
            "confidence_method": self.confidence_method,
            "confidence_method_version": self.confidence_method_version,
            "evidence_completeness": self.evidence_completeness,
            "match_status": self.match_status,
            "severity": self.severity,
            "priority": self.priority,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "source_plugin": self.source_plugin,
            "supporting_evidence": [item.to_dict() for item in self.supporting_evidence],
            "conflicting_evidence": [item.to_dict() for item in self.conflicting_evidence],
            "support_contributions": [item.to_dict() for item in self.support_contributions],
            "contradiction_contributions": [item.to_dict() for item in self.contradiction_contributions],
            "missing_contributions": [item.to_dict() for item in self.missing_contributions],
            "limitations": list(self.limitations),
            "participates_in_ranking": self.participates_in_ranking,
        }
