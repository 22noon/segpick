from __future__ import annotations
from pathlib import Path
from typing import Any, Iterable
import yaml
from segpick.reasoning.rules import RuleCondition
from .schema import EvidencePatternDefinition

SCHEMA_VERSION = 1

def _text(value: Any, field: str, source: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{source}: evidence pattern field '{field}' must be non-empty text")
    return value.strip()

def _condition(raw: Any, source: str, sid: str) -> RuleCondition:
    if not isinstance(raw, dict):
        raise ValueError(f"{source}: evidence pattern '{sid}' conditions must be mappings")
    kinds = [k for k in ("observation", "finding") if k in raw]
    if len(kinds) != 1:
        raise ValueError(f"{source}: evidence pattern '{sid}' condition must define one observation or finding")
    kind = kinds[0]
    return RuleCondition(kind=kind, value=_text(raw[kind], kind, source), source=raw.get("source"))

def _conditions(raw: Any, source: str, sid: str) -> tuple[RuleCondition, ...]:
    if raw is None: return ()
    if not isinstance(raw, list): raise ValueError(f"{source}: evidence pattern '{sid}' conditions must be a list")
    return tuple(_condition(x, source, sid) for x in raw)

def load_knowledge_file(path: str | Path, *, source_label: str | None = None) -> tuple[EvidencePatternDefinition, ...]:
    p = Path(path); source = source_label or str(p)
    raw = yaml.safe_load(p.read_text()) or {}
    if not isinstance(raw, dict) or raw.get("version", 1) != SCHEMA_VERSION:
        raise ValueError(f"{source}: unsupported knowledge schema")
    modules = []
    for item in raw.get("evidence_patterns", []):
        sid = _text(item.get("id"), "id", source)
        requires = _conditions(item.get("requires"), source, sid)
        if not requires: raise ValueError(f"{source}: evidence pattern '{sid}' requires at least one condition")
        actions = item.get("suggested_actions", [])
        modules.append(EvidencePatternDefinition(
            pattern_id=sid, title=_text(item.get("title"), "title", source),
            category=_text(item.get("category"), "category", source),
            scope=_text(item.get("scope"), "scope", source),
            severity=_text(item.get("severity"), "severity", source),
            base_confidence=_text(item.get("base_confidence"), "base_confidence", source),
            interpretation=_text(item.get("interpretation"), "interpretation", source),
            requires=requires, supports=_conditions(item.get("supports"), source, sid),
            conflicts=_conditions(item.get("conflicts"), source, sid),
            suggested_actions=tuple(str(x).strip() for x in actions),
            references=tuple(str(x).strip() for x in item.get("references", [])), source=source,
        ))
    return tuple(modules)

def load_active_evidence_patterns(user_files: Iterable[str | Path] = ()) -> tuple[tuple[EvidencePatternDefinition, ...], tuple[EvidencePatternDefinition, ...]]:
    builtin = load_knowledge_file(Path(__file__).with_name("default_evidence_patterns.yml"), source_label="builtin:default_evidence_patterns.yml")
    all_items = list(builtin)
    for path in user_files: all_items.extend(load_knowledge_file(path))
    seen=set()
    for item in all_items:
        if item.pattern_id in seen: raise ValueError(f"Duplicate evidence pattern id '{item.pattern_id}'")
        seen.add(item.pattern_id)
    return tuple(x for x in all_items if x.scope=="candidate"), tuple(x for x in all_items if x.scope=="gene")
