from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, TYPE_CHECKING

from segpick.models.observation import EvidenceObservation

if TYPE_CHECKING:
    from segpick.models import CandidateContig


@dataclass(frozen=True, slots=True)
class PluginMeasurement:
    name: str
    value: Any
    unit: str | None = None
    provenance: str | None = None
    attributes: tuple[tuple[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class EvidencePluginResult:
    measurements: tuple[PluginMeasurement, ...] = ()
    observations: tuple[EvidenceObservation, ...] = ()


class EvidenceChannel(Protocol):
    channel_id: str

    def evaluate(self, candidate: CandidateContig) -> EvidencePluginResult:
        """Return immutable evidence produced for one candidate."""
