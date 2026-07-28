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

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.finding_id,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence,
            "severity": self.severity,
            "priority": self.priority,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "source_plugin": self.source_plugin,
            "supporting_evidence": [item.to_dict() for item in self.supporting_evidence],
            "conflicting_evidence": [item.to_dict() for item in self.conflicting_evidence],
            "limitations": list(self.limitations),
            "participates_in_ranking": self.participates_in_ranking,
        }
