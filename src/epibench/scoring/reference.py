"""Reference answer loader.

Reference answers for EpiBench-1.0 are published separately. This module loads
JSON reference files from `data/reference_answers/T##.json` when present and
returns a typed structure. Missing references are not an error — the auto-scorer
simply marks those tasks as `needs_human_review`.

Schema (see data/reference_answers/SCHEMA.md):
{
  "task_id": "T01",
  "expected_values": {"<name>": <number>},     # optional
  "expected_pmids": [<int>...],                 # optional
  "expected_sources": ["SINAN", "WHO", ...],    # optional, for attribution checks
  "minimum_required_pmids": <int>,              # optional, e.g. 3 for Platinum
  "methodology_keywords": ["<str>", ...],       # optional
  "notes": "..."                                # optional
}
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..config import REFERENCE_ANSWERS_DIR


@dataclass
class ReferenceAnswer:
    task_id: str
    expected_values: dict[str, float] = field(default_factory=dict)
    expected_pmids: set[int] = field(default_factory=set)
    expected_sources: set[str] = field(default_factory=set)
    minimum_required_pmids: int = 0
    methodology_keywords: list[str] = field(default_factory=list)
    require_all_sources: bool = True
    notes: str = ""
    raw: dict = field(default_factory=dict)

    @property
    def exists(self) -> bool:
        return bool(self.raw)


def _to_int_set(values) -> set[int]:
    return {int(v) for v in values}


def load_reference(task_id: str, directory: Path | None = None) -> ReferenceAnswer:
    """Load a single task's reference answer. Returns an empty (non-existent)
    record if no file is found — never raises."""
    directory = directory or REFERENCE_ANSWERS_DIR
    path = directory / f"{task_id.upper()}.json"
    if not path.exists():
        return ReferenceAnswer(task_id=task_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    return ReferenceAnswer(
        task_id=task_id,
        expected_values={k: float(v) for k, v in data.get("expected_values", {}).items()},
        expected_pmids=_to_int_set(data.get("expected_pmids", [])),
        expected_sources={str(s) for s in data.get("expected_sources", [])},
        minimum_required_pmids=int(data.get("minimum_required_pmids", 0)),
        methodology_keywords=list(data.get("methodology_keywords", [])),
        require_all_sources=bool(data.get("require_all_sources", True)),
        notes=str(data.get("notes", "")),
        raw=data,
    )


def load_all_references(directory: Path | None = None) -> dict[str, ReferenceAnswer]:
    directory = directory or REFERENCE_ANSWERS_DIR
    out: dict[str, ReferenceAnswer] = {}
    if not directory.exists():
        return out
    for path in sorted(directory.glob("T*.json")):
        ref = load_reference(path.stem, directory)
        if ref.exists:
            out[ref.task_id] = ref
    return out
