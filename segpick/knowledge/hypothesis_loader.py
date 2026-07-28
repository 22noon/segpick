from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import yaml

from .hypothesis_schema import HypothesisModule

SCHEMA_VERSION = 1


def _text(value: Any, field: str, source: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{source}: hypothesis field '{field}' must be non-empty text")
    return value.strip()


def load_hypothesis_file(path: str | Path, *, source_label: str | None = None) -> tuple[HypothesisModule, ...]:
    p = Path(path)
    source = source_label or str(p)
    raw = yaml.safe_load(p.read_text()) or {}
    if not isinstance(raw, dict) or raw.get("version", 1) != SCHEMA_VERSION:
        raise ValueError(f"{source}: unsupported knowledge schema")
    modules: list[HypothesisModule] = []
    for item in raw.get("hypotheses", []) or []:
        hid = _text(item.get("id"), "id", source)
        supported_by = tuple(str(x).strip() for x in item.get("supported_by", []) if str(x).strip())
        if not supported_by:
            raise ValueError(f"{source}: hypothesis '{hid}' requires at least one supported_by scenario")
        modules.append(HypothesisModule(
            hypothesis_id=hid,
            title=_text(item.get("title"), "title", source),
            category=_text(item.get("category"), "category", source),
            scope=_text(item.get("scope"), "scope", source),
            severity=_text(item.get("severity"), "severity", source),
            base_confidence=_text(item.get("base_confidence"), "base_confidence", source),
            explanation=_text(item.get("explanation"), "explanation", source),
            supported_by=supported_by,
            contradicted_by=tuple(str(x).strip() for x in item.get("contradicted_by", []) if str(x).strip()),
            minimum_support=int(item.get("minimum_support", 1)),
            recommended_actions=tuple(str(x).strip() for x in item.get("recommended_actions", []) if str(x).strip()),
            references=tuple(str(x).strip() for x in item.get("references", []) if str(x).strip()),
            source=source,
        ))
    return tuple(modules)


def load_active_hypotheses(user_files: Iterable[str | Path] = ()) -> tuple[tuple[HypothesisModule, ...], tuple[HypothesisModule, ...]]:
    builtin = load_hypothesis_file(
        Path(__file__).with_name("default_hypotheses.yml"),
        source_label="builtin:default_hypotheses.yml",
    )
    all_items = list(builtin)
    for path in user_files:
        all_items.extend(load_hypothesis_file(path))
    seen: set[str] = set()
    for item in all_items:
        if item.hypothesis_id in seen:
            raise ValueError(f"Duplicate hypothesis id '{item.hypothesis_id}'")
        seen.add(item.hypothesis_id)
    return (
        tuple(x for x in all_items if x.scope == "candidate"),
        tuple(x for x in all_items if x.scope == "gene"),
    )
