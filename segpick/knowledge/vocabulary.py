from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class VocabularyEntry:
    identifier: str
    display_name: str
    description: str = ""
    category: str = ""


@dataclass(frozen=True, slots=True)
class ConditionDisplay:
    identifier: str
    display_name: str
    description: str
    source: str | None
    source_display_name: str | None
    kind: str


def _humanise_identifier(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()


def _humanise_source(value: str | None) -> str | None:
    if value is None:
        return None
    aliases = {
        "read_coverage": "Read coverage",
        "structural_alignment": "Structural alignment",
        "cross_evidence": "Combined read and structural evidence",
        "orf_structure": "ORF structure",
        "protein_alignment": "Protein alignment",
        "protein_continuity": "Protein continuity",
        "diamond": "Protein similarity search",
    }
    return aliases.get(value, _humanise_identifier(value))


def load_vocabulary(path: str | Path | None = None) -> dict[str, VocabularyEntry]:
    vocabulary_path = Path(path) if path is not None else Path(__file__).with_name("observation_vocabulary.yml")
    raw: dict[str, Any] = yaml.safe_load(vocabulary_path.read_text()) or {}
    if raw.get("version", 1) != 1:
        raise ValueError(f"{vocabulary_path}: unsupported vocabulary schema")

    entries: dict[str, VocabularyEntry] = {}
    for identifier, item in (raw.get("observations") or {}).items():
        if not isinstance(item, dict):
            raise ValueError(f"{vocabulary_path}: observation '{identifier}' must be a mapping")
        entries[identifier] = VocabularyEntry(
            identifier=identifier,
            display_name=str(item.get("display_name") or _humanise_identifier(identifier)).strip(),
            description=str(item.get("description") or "").strip(),
            category=str(item.get("category") or "").strip(),
        )
    return entries


def describe_condition(label: str, vocabulary: dict[str, VocabularyEntry] | None = None) -> ConditionDisplay:
    """Convert a stable rule label into user-facing text.

    Labels retain their machine-readable form, for example
    ``observation:weak_orf_terminal_support@read_coverage``. The dashboard uses
    the returned display fields instead of exposing that representation.
    """

    vocabulary = vocabulary if vocabulary is not None else load_vocabulary()
    kind, separator, remainder = label.partition(":")
    if not separator:
        kind, remainder = "observation", label
    identifier, source_separator, source = remainder.partition("@")
    source_value = source if source_separator else None

    if kind == "finding":
        display_name = identifier
        description = "Biological finding supporting this evidence pattern."
    else:
        entry = vocabulary.get(identifier)
        display_name = entry.display_name if entry else _humanise_identifier(identifier)
        description = entry.description if entry else ""

    return ConditionDisplay(
        identifier=label,
        display_name=display_name,
        description=description,
        source=source_value,
        source_display_name=_humanise_source(source_value),
        kind=kind,
    )
