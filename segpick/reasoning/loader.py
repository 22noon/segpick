from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml

from .rules import HypothesisRule, RuleCondition

RULE_SCHEMA_VERSION = 1

_ALLOWED_RULE_KEYS = {
    "id",
    "title",
    "description",
    "category",
    "scope",
    "severity",
    "base_confidence",
    "summary",
    "requires",
    "supports",
    "conflicts",
    "references",
}
_ALLOWED_SCOPES = {"candidate", "gene"}
_ALLOWED_CONFIDENCE = {"low", "moderate", "high"}
_ALLOWED_CONDITION_KEYS = {"observation", "finding", "source"}


def _nonempty_text(value: Any, field: str, source: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{source}: rule field '{field}' must be non-empty text")
    return value.strip()


def _parse_condition(raw: Any, source: str, rule_id: str) -> RuleCondition:
    if not isinstance(raw, dict):
        raise ValueError(f"{source}: rule '{rule_id}' conditions must be mappings")
    unknown = set(raw) - _ALLOWED_CONDITION_KEYS
    if unknown:
        raise ValueError(
            f"{source}: rule '{rule_id}' has unknown condition fields: "
            + ", ".join(sorted(unknown))
        )
    kinds = [kind for kind in ("observation", "finding") if kind in raw]
    if len(kinds) != 1:
        raise ValueError(
            f"{source}: rule '{rule_id}' condition must define exactly one of "
            "'observation' or 'finding'"
        )
    kind = kinds[0]
    value = _nonempty_text(raw[kind], kind, source)
    condition_source = raw.get("source")
    if condition_source is not None:
        condition_source = _nonempty_text(condition_source, "source", source)
    return RuleCondition(kind=kind, value=value, source=condition_source)


def _parse_conditions(
    raw: Any,
    field: str,
    source: str,
    rule_id: str,
) -> tuple[RuleCondition, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError(f"{source}: rule '{rule_id}' field '{field}' must be a list")
    return tuple(_parse_condition(item, source, rule_id) for item in raw)


def _parse_rule(raw: Any, source: str) -> HypothesisRule:
    if not isinstance(raw, dict):
        raise ValueError(f"{source}: every rule must be a mapping")
    unknown = set(raw) - _ALLOWED_RULE_KEYS
    if unknown:
        raise ValueError(
            f"{source}: unknown rule fields: " + ", ".join(sorted(unknown))
        )

    rule_id = _nonempty_text(raw.get("id"), "id", source)
    scope = _nonempty_text(raw.get("scope"), "scope", source)
    if scope not in _ALLOWED_SCOPES:
        raise ValueError(
            f"{source}: rule '{rule_id}' has unsupported scope '{scope}'"
        )
    confidence = _nonempty_text(
        raw.get("base_confidence"), "base_confidence", source
    )
    if confidence not in _ALLOWED_CONFIDENCE:
        raise ValueError(
            f"{source}: rule '{rule_id}' has unsupported base confidence "
            f"'{confidence}'"
        )

    references_raw = raw.get("references", [])
    if not isinstance(references_raw, list) or not all(
        isinstance(item, str) and item.strip() for item in references_raw
    ):
        raise ValueError(
            f"{source}: rule '{rule_id}' field 'references' must be a list of text"
        )

    requires = _parse_conditions(raw.get("requires"), "requires", source, rule_id)
    if not requires:
        raise ValueError(f"{source}: rule '{rule_id}' must define at least one requirement")

    return HypothesisRule(
        rule_id=rule_id,
        title=_nonempty_text(raw.get("title"), "title", source),
        description=str(raw.get("description", "")).strip(),
        category=_nonempty_text(raw.get("category"), "category", source),
        scope=scope,
        severity=_nonempty_text(raw.get("severity"), "severity", source),
        base_confidence=confidence,
        summary=_nonempty_text(raw.get("summary"), "summary", source),
        requires=requires,
        supports=_parse_conditions(raw.get("supports"), "supports", source, rule_id),
        conflicts=_parse_conditions(raw.get("conflicts"), "conflicts", source, rule_id),
        references=tuple(item.strip() for item in references_raw),
        source=source,
    )


def load_rule_file(path: str | Path, *, source_label: str | None = None) -> tuple[HypothesisRule, ...]:
    rule_path = Path(path)
    source = source_label or str(rule_path)
    if not rule_path.exists():
        raise FileNotFoundError(f"Rule file not found: {rule_path}")
    raw = yaml.safe_load(rule_path.read_text()) or {}
    if isinstance(raw, list):
        rule_data = raw
    elif isinstance(raw, dict):
        unknown_root = set(raw) - {"version", "rules"}
        if unknown_root:
            raise ValueError(
                f"{source}: unknown top-level fields: "
                + ", ".join(sorted(unknown_root))
            )
        version = raw.get("version", RULE_SCHEMA_VERSION)
        if version != RULE_SCHEMA_VERSION:
            raise ValueError(f"{source}: unsupported rule schema version {version!r}")
        rule_data = raw.get("rules", [])
    else:
        raise ValueError(f"{source}: YAML root must be a mapping or list")
    if not isinstance(rule_data, list):
        raise ValueError(f"{source}: 'rules' must be a list")
    return tuple(_parse_rule(item, source) for item in rule_data)


def merge_rules(*rule_sets: Iterable[HypothesisRule]) -> tuple[HypothesisRule, ...]:
    merged: list[HypothesisRule] = []
    seen: dict[str, str] = {}
    for rule_set in rule_sets:
        for rule in rule_set:
            if rule.rule_id in seen:
                raise ValueError(
                    f"Duplicate rule id '{rule.rule_id}' in {rule.source}; "
                    f"already defined in {seen[rule.rule_id]}"
                )
            seen[rule.rule_id] = rule.source
            merged.append(rule)
    return tuple(merged)


def split_rules_by_scope(
    rules: Iterable[HypothesisRule],
) -> tuple[tuple[HypothesisRule, ...], tuple[HypothesisRule, ...]]:
    all_rules = tuple(rules)
    return (
        tuple(rule for rule in all_rules if rule.scope == "candidate"),
        tuple(rule for rule in all_rules if rule.scope == "gene"),
    )


def load_active_rules(
    user_rule_files: Iterable[str | Path] = (),
) -> tuple[tuple[HypothesisRule, ...], tuple[HypothesisRule, ...]]:
    builtin_path = Path(__file__).with_name("default_rules.yml")
    builtin = load_rule_file(builtin_path, source_label="builtin:default_rules.yml")
    user_sets = tuple(load_rule_file(path) for path in user_rule_files)
    return split_rules_by_scope(merge_rules(builtin, *user_sets))
