"""Persistence: per-run JSON files + a cumulative leaderboard.

Run layout (under `results/`):
    runs/<YYYYmmddTHHMMSS>_<model>/
        run.json        full manifest: model, timestamps, totals, tier, per-task summary
        summary.csv     one row per task
        tasks/T##.json  full per-task record (prompt, response, scores, flags)
    leaderboard.json
    leaderboard.csv
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .scoring.auto import AutoScoreResult
from .scoring.rubric import ScoreBreakdown, classify_total
from .tasks import TOTAL_MAX_POINTS


def _sanitize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:80]


def _timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


@dataclass
class TaskRecord:
    task_id: str
    task_name: str
    level: str
    domain: str
    max_points: int
    prompt: str
    response_text: str
    latency_seconds: float
    token_usage: dict[str, int]
    finish_reason: str | None
    score: ScoreBreakdown
    auto: AutoScoreResult | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "level": self.level,
            "domain": self.domain,
            "max_points": self.max_points,
            "prompt": self.prompt,
            "response_text": self.response_text,
            "latency_seconds": round(self.latency_seconds, 4),
            "token_usage": self.token_usage,
            "finish_reason": self.finish_reason,
            "error": self.error,
            "score": {
                "final": self.score.final,
                "raw_positive": round(self.score.raw_positive, 4),
                "penalties": {k: v for k, v in self.score.penalties_applied.items()},
                "privacy_violation": self.score.privacy_violation,
                "needs_human_review": self.score.needs_human_review,
                "category_scores": self.score.category_scores.as_dict(),
                "notes": self.score.notes,
            },
            "auto": _auto_to_dict(self.auto) if self.auto else None,
        }
        return d


def _auto_to_dict(auto: AutoScoreResult) -> dict[str, Any]:
    return {
        "extracted_values": auto.extracted_values,
        "extracted_pmids": sorted(auto.extracted_pmids),
        "verified_pmids": {str(k): v for k, v in auto.verified_pmids.items()},
        "penalties": {k: v for k, v in auto.penalties.items()},
        "needs_human_review": auto.needs_human_review,
        "notes": auto.notes,
        "category_scores": auto.category_scores.as_dict(),
    }


@dataclass
class RunManifest:
    run_id: str
    model: str
    created_at: str
    tasks: list[TaskRecord] = field(default_factory=list)

    @property
    def total_score(self) -> float:
        return round(sum(t.score.final for t in self.tasks), 4)

    @property
    def max_possible(self) -> int:
        return sum(t.max_points for t in self.tasks) or TOTAL_MAX_POINTS

    @property
    def privacy_violation(self) -> bool:
        return any(t.score.privacy_violation for t in self.tasks)

    @property
    def tier(self) -> str:
        return classify_total(self.total_score, privacy_violation=self.privacy_violation).value

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "model": self.model,
            "created_at": self.created_at,
            "total_score": self.total_score,
            "max_possible": self.max_possible,
            "percentage": round(100.0 * self.total_score / self.max_possible, 2)
            if self.max_possible
            else 0.0,
            "tier": self.tier,
            "privacy_violation": self.privacy_violation,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "task_name": t.task_name,
                    "level": t.level,
                    "max_points": t.max_points,
                    "score": t.score.final,
                    "needs_human_review": t.score.needs_human_review,
                    "privacy_violation": t.score.privacy_violation,
                    "error": t.error,
                }
                for t in self.tasks
            ],
        }


def new_run_dir(model_display: str, base: Path) -> Path:
    slug = _timestamp_slug() + "_" + _sanitize(model_display)
    run_dir = base / "runs" / slug
    (run_dir / "tasks").mkdir(parents=True, exist_ok=True)
    return run_dir


def write_run(manifest: RunManifest, results_dir: Path) -> Path:
    """Write run.json + summary.csv + per-task JSON. Returns the run directory."""
    results_dir.mkdir(parents=True, exist_ok=True)
    run_dir = new_run_dir(manifest.model, results_dir)

    (run_dir / "run.json").write_text(
        json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )

    with (run_dir / "summary.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "task_id",
                "task_name",
                "level",
                "max_points",
                "score",
                "percentage",
                "needs_human_review",
                "privacy_violation",
                "error",
            ]
        )
        for t in manifest.tasks:
            pct = round(100.0 * t.score.final / t.max_points, 2) if t.max_points else 0.0
            writer.writerow(
                [
                    t.task_id,
                    t.task_name,
                    t.level,
                    t.max_points,
                    t.score.final,
                    pct,
                    t.score.needs_human_review,
                    t.score.privacy_violation,
                    t.error or "",
                ]
            )

    for t in manifest.tasks:
        (run_dir / "tasks" / f"{t.task_id}.json").write_text(
            json.dumps(t.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )

    _update_leaderboard(manifest, results_dir)
    return run_dir


def _update_leaderboard(manifest: RunManifest, results_dir: Path) -> None:
    entry = {
        "run_id": manifest.run_id,
        "model": manifest.model,
        "created_at": manifest.created_at,
        "total_score": manifest.total_score,
        "max_possible": manifest.max_possible,
        "percentage": round(100.0 * manifest.total_score / manifest.max_possible, 2)
        if manifest.max_possible
        else 0.0,
        "tier": manifest.tier,
        "privacy_violation": manifest.privacy_violation,
    }

    json_path = results_dir / "leaderboard.json"
    entries: list[dict[str, Any]] = []
    if json_path.exists():
        try:
            entries = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            entries = []
    entries.append(entry)
    json_path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    csv_path = results_dir / "leaderboard.csv"
    fields = [
        "run_id",
        "model",
        "created_at",
        "total_score",
        "max_possible",
        "percentage",
        "tier",
        "privacy_violation",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(entries)


def load_leaderboard(results_dir: Path) -> list[dict[str, Any]]:
    json_path = results_dir / "leaderboard.json"
    if not json_path.exists():
        return []
    return json.loads(json_path.read_text(encoding="utf-8"))


__all__ = [
    "TaskRecord",
    "RunManifest",
    "new_run_dir",
    "write_run",
    "load_leaderboard",
]
