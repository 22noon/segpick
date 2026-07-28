from __future__ import annotations
from dataclasses import dataclass
from .engine import CrossEvidenceContext, register_rule
from segpick.models import CrossEvidenceFinding


def _confidence(*levels: str) -> str:
    rank = {"high": 3, "moderate": 2, "low": 1, "not_assessable": 0}
    value = min((rank.get(x, 1) for x in levels), default=1)
    return {3: "high", 2: "moderate", 1: "low", 0: "low"}[value]

@dataclass(frozen=True)
class DeclarativeRule:
    rule_id: str
    version: str
    source_plugin: str
    required_channels: frozenset[str]
    required_findings: tuple[tuple[str, str], ...]
    output_id: str
    title: str
    description: str
    severity: str
    priority: int
    limitations: tuple[str, ...] = ()

    def evaluate(self, context: CrossEvidenceContext):
        refs = tuple(context.finding(*key) for key in self.required_findings)
        if any(item is None for item in refs):
            return ()
        levels = tuple(context.assessment(channel).confidence.level for channel in self.required_channels if context.assessment(channel))
        return (CrossEvidenceFinding(self.output_id, self.title, self.description, _confidence(*levels), self.severity, self.priority, self.rule_id, self.version, self.source_plugin, tuple(item for item in refs if item), limitations=self.limitations),)

for rule in (
    DeclarativeRule("segpick:read_supported_reference_absent_sequence", "1.0", "segpick.core", frozenset({"reference_compatibility", "read_evidence"}), (("reference_compatibility", "unsupported_internal_candidate_region"), ("read_evidence", "read_evidence_summary")), "segpick:read_supported_reference_absent_sequence", "Reference-absent sequence is supported by reads", "An internal candidate interval absent from the closest reference occurs in a candidate whose biologically relevant region is supported by read coverage. This favours genuine divergence or insertion over an unsupported assembly addition.", "information", 90, ("Read support is currently assessed across the biologically relevant region rather than both insertion junctions specifically.",)),
    DeclarativeRule("segpick:reference_relative_rearrangement", "1.0", "segpick.core", frozenset({"reference_compatibility", "structural_integrity"}), (("reference_compatibility", "reference_block_order_disrupted"), ("structural_integrity", "structural_integrity_summary")), "segpick:reference_relative_rearrangement", "Reference-relative rearrangement with coherent assembly structure", "Reference alignment blocks are reordered while the independent structural channel remains coherent, supporting review for genuine reference-relative structural variation.", "review", 80),
    DeclarativeRule("segpick:reference_relative_inversion", "1.0", "segpick.core", frozenset({"reference_compatibility", "structural_integrity"}), (("reference_compatibility", "unexpected_reference_orientation_switch"), ("structural_integrity", "structural_integrity_summary")), "segpick:reference_relative_inversion", "Reference-relative inversion with coherent assembly structure", "A reference-relative orientation switch is present without independent evidence of structural incoherence.", "review", 85),
):
    register_rule(rule)
