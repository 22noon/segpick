from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.hypotheses import attach_biological_hypotheses
from segpick.evidence_plugins import (
    EvidencePluginRegistry,
    EvidencePluginResult,
    PluginMeasurement,
)
from segpick.models import CandidateContig, ContigMetadata, EvidenceObservation, Gene, Sample
from segpick.reasoning.rules import HypothesisRule, RuleCondition


class JunctionEvidenceChannel:
    channel_id = "junction_support"

    def evaluate(self, candidate):
        return EvidencePluginResult(
            measurements=(
                PluginMeasurement(
                    name="junction_spanning_reads",
                    value=18,
                    unit="reads",
                    provenance="plugin-test.tsv",
                ),
            ),
            observations=(
                EvidenceObservation(
                    observation_type="junction_supported",
                    source="plugin:junction_support",
                    description="Reads span the candidate junction.",
                    attributes={"count": 18},
                ),
            ),
        )


def _sample():
    candidate = CandidateContig(
        id="contig_1",
        record=SeqRecord(Seq("A" * 100), id="contig_1"),
        metadata=ContigMetadata(segment="1", score=10.0, confidence=0.9, cluster="a"),
    )
    gene = Gene(name="VP1", segment="1", candidates=[candidate])
    return Sample(name="sample", genes={"VP1": gene}), candidate


def test_plugin_observation_can_trigger_hypothesis_and_enter_graph():
    sample, candidate = _sample()
    registry = EvidencePluginRegistry()
    registry.register(JunctionEvidenceChannel())
    rule = HypothesisRule(
        rule_id="junction_supported_structure",
        title="Junction-supported structure",
        category="assembly_structure",
        scope="candidate",
        severity="informational",
        base_confidence="moderate",
        summary="The proposed structure has direct junction support.",
        requires=(RuleCondition("observation", "junction_supported", "plugin:junction_support"),),
    )

    attach_biological_hypotheses(sample, candidate_rules=(rule,), gene_rules=(), plugin_registry=registry)

    assert candidate.analysis.hypotheses[0].rule_id == "junction_supported_structure"
    graph = candidate.analysis.reasoning_graph
    assert graph is not None
    assert graph.measurements[0].channel == "junction_support"
    assert graph.observations[0].source == "plugin:junction_support"
    assert graph.observations[0].measurement_ids == (graph.measurements[0].id,)
    assert graph.hypotheses[0].supporting_ids == (graph.observations[0].id,)
    graph.validate()


def test_registry_rejects_duplicate_channel_ids():
    registry = EvidencePluginRegistry()
    registry.register(JunctionEvidenceChannel())
    try:
        registry.register(JunctionEvidenceChannel())
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("duplicate plugin channel should be rejected")


def test_hypothesis_state_is_preserved_in_reasoning_graph():
    sample, candidate = _sample()
    candidate.analysis.observations = (
        EvidenceObservation(
            observation_type="duplicated_reference_mapping",
            source="reference_compatibility",
            description="Repeated reference coordinates.",
        ),
        EvidenceObservation(
            observation_type="junction_supported",
            source="plugin:junction_support",
            description="Reads span the candidate junction.",
        ),
    )
    attach_biological_hypotheses(sample, plugin_registry=None)

    hypotheses = {node.rule_id: node for node in candidate.analysis.reasoning_graph.hypotheses}
    assert hypotheses["possible_repeated_sequence_architecture"].state == "supported"
    assert hypotheses["possible_repeat_associated_assembly_artefact"].state == "challenged"


def test_hypothesis_metadata_and_rule_provenance_enter_graph():
    sample, candidate = _sample()
    candidate.analysis.observations = (
        EvidenceObservation(
            observation_type="junction_supported",
            source="plugin:junction_support",
            description="Reads span the candidate junction.",
        ),
    )
    rule = HypothesisRule(
        rule_id="junction_supported_structure",
        title="Junction-supported structure",
        category="assembly_structure",
        scope="candidate",
        severity="review",
        base_confidence="moderate",
        summary="The proposed structure has direct junction support.",
        description="Tests preservation of declarative rule provenance.",
        references=("doi:10.0000/example",),
        source="user:test-rules.yml",
        requires=(RuleCondition("observation", "junction_supported", "plugin:junction_support"),),
    )

    attach_biological_hypotheses(
        sample, candidate_rules=(rule,), gene_rules=(), plugin_registry=None
    )

    node = candidate.analysis.reasoning_graph.hypotheses[0]
    assert node.category == "assembly_structure"
    assert node.scope == "candidate"
    assert node.severity == "review"
    assert node.rule_source == "user:test-rules.yml"
    assert node.rule_description == "Tests preservation of declarative rule provenance."
    assert node.rule_references == ("doi:10.0000/example",)
    assert candidate.analysis.reasoning_graph.to_dict()["hypotheses"][0]["rule_source"] == "user:test-rules.yml"
