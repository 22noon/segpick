from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiagnosticCheck:
    check_id: str
    title: str
    status: str
    detail: str = ""
    value: object | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.check_id,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "value": self.value,
        }


@dataclass(frozen=True, slots=True)
class AssessmentDiagnostics:
    checks: tuple[DiagnosticCheck, ...] = ()
    stop_reason: str | None = None

    @property
    def has_failure(self) -> bool:
        return any(check.status == "fail" for check in self.checks)

    def to_dict(self) -> dict[str, object]:
        return {
            "checks": [check.to_dict() for check in self.checks],
            "stop_reason": self.stop_reason,
            "has_failure": self.has_failure,
        }


@dataclass(frozen=True, slots=True)
class ConfidenceFactor:
    name: str
    value: float | int | str | bool | None
    contribution: float | None
    interpretation: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "value": self.value,
            "contribution": self.contribution,
            "interpretation": self.interpretation,
        }


@dataclass(frozen=True, slots=True)
class ConfidenceAssessment:
    level: str
    score: float | None
    method: str
    version: str
    factors: tuple[ConfidenceFactor, ...] = ()
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "score": self.score,
            "method": self.method,
            "version": self.version,
            "factors": [factor.to_dict() for factor in self.factors],
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True)
class EvidenceFinding:
    finding_id: str
    title: str
    description: str
    severity: str = "information"
    priority: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.finding_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "priority": self.priority,
        }


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    channel_id: str
    channel_title: str
    channel_version: str
    status: str
    score: float | None
    confidence: ConfidenceAssessment
    key_finding: EvidenceFinding
    supporting_findings: tuple[EvidenceFinding, ...] = ()
    measurements: tuple[dict[str, object], ...] = ()
    limitations: tuple[str, ...] = ()
    participates_in_ranking: bool = False
    diagnostics: AssessmentDiagnostics | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "channel_id": self.channel_id,
            "channel_title": self.channel_title,
            "channel_version": self.channel_version,
            "status": self.status,
            "score": self.score,
            "confidence": self.confidence.to_dict(),
            "key_finding": self.key_finding.to_dict(),
            "supporting_findings": [item.to_dict() for item in self.supporting_findings],
            "measurements": list(self.measurements),
            "limitations": list(self.limitations),
            "participates_in_ranking": self.participates_in_ranking,
            "diagnostics": self.diagnostics.to_dict() if self.diagnostics is not None else None,
        }
