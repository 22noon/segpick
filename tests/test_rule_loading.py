from pathlib import Path

import pytest

from segpick.reasoning import load_active_rules, load_rule_file


def write_rules(path: Path, text: str) -> Path:
    path.write_text(text)
    return path


def test_builtin_rules_are_loaded_from_yaml():
    candidate_rules, gene_rules = load_active_rules()

    assert {rule.rule_id for rule in candidate_rules} == {
        "possible_assembly_interruption",
        "divergent_structurally_supported_protein",
        "reference_supported_architecture",
        "possible_repeated_sequence_architecture",
        "possible_repeat_associated_assembly_artefact",
    }
    assert {rule.rule_id for rule in gene_rules} == {"possible_split_assembly"}
    assert all(rule.source == "builtin:default_rules.yml" for rule in (*candidate_rules, *gene_rules))


def test_user_rule_file_extends_builtins(tmp_path):
    rule_file = write_rules(
        tmp_path / "rules.yml",
        """
version: 1
rules:
  - id: custom_complete_protein
    title: Custom complete protein hypothesis
    description: Laboratory-specific interpretation.
    category: custom
    scope: candidate
    severity: informational
    base_confidence: moderate
    summary: Complete protein matches the custom rule.
    requires:
      - finding: Complete protein recovered
    references:
      - PMID:12345678
""",
    )

    candidate_rules, gene_rules = load_active_rules((rule_file,))

    assert len(candidate_rules) == 6
    custom = next(rule for rule in candidate_rules if rule.rule_id == "custom_complete_protein")
    assert custom.source == str(rule_file)
    assert custom.references == ("PMID:12345678",)
    assert len(gene_rules) == 1


def test_duplicate_user_rule_id_is_rejected(tmp_path):
    rule_file = write_rules(
        tmp_path / "duplicate.yml",
        """
rules:
  - id: possible_split_assembly
    title: Duplicate
    category: assembly
    scope: gene
    severity: warning
    base_confidence: high
    summary: Duplicate rule.
    requires:
      - finding: Possible split assembly
""",
    )

    with pytest.raises(ValueError, match="Duplicate rule id 'possible_split_assembly'"):
        load_active_rules((rule_file,))


def test_invalid_condition_schema_is_rejected(tmp_path):
    rule_file = write_rules(
        tmp_path / "invalid.yml",
        """
rules:
  - id: invalid
    title: Invalid
    category: test
    scope: candidate
    severity: review
    base_confidence: moderate
    summary: Invalid condition.
    requires:
      - observation: coverage_drop
        finding: Complete protein recovered
""",
    )

    with pytest.raises(ValueError, match="exactly one"):
        load_rule_file(rule_file)
