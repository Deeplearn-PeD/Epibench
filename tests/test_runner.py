from __future__ import annotations

import json

from epibench.models.base import DummyBackend, ModelResponse
from epibench.runner import run_benchmark
from epibench.scoring.rubric import classify_total
from epibench.storage import load_leaderboard, write_run
from epibench.tasks import all_tasks


class _ScriptedBackend(DummyBackend):
    """DummyBackend that emits a fixed response containing a couple of PMIDs
    and a labeled number, so the auto-scorer has something to chew on."""

    def __init__(self, model: str, payload: str) -> None:
        super().__init__(model)
        self.display_name = f"scripted:{model}"
        self._payload = payload

    def complete(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        return ModelResponse(text=self._payload, finish_reason="scripted")


def test_end_to_end_run_persists_well_formed_json(tmp_path, monkeypatch):
    # Force network scoring off so PMID verification is deterministic.
    monkeypatch.setenv("EPIBENCH_NETWORK_SCORING", "0")
    monkeypatch.setenv("EPIBENCH_RESULTS_DIR", str(tmp_path))

    payload = (
        "SINAN, SIM and SINASC datasets are available.\n"
        "Incidence rate: 100.0 per 100k inhabitants.\n"
        "See PMID: 36631231 for context."
    )
    backend = _ScriptedBackend("demo", payload)

    tasks = all_tasks()[:3]  # T01..T03
    manifest = run_benchmark(tasks, backend)
    run_dir = write_run(manifest, tmp_path)

    # ---- run.json ------------------------------------------------------- #
    run_json = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert run_json["model"] == "scripted:demo"
    assert len(run_json["tasks"]) == 3
    assert {t["task_id"] for t in run_json["tasks"]} == {"T01", "T02", "T03"}
    assert run_json["max_possible"] == sum(t.max_points for t in tasks)
    assert 0 <= run_json["total_score"] <= run_json["max_possible"]
    assert run_json["tier"] in {b.value for b in classify_total(0).__class__}

    # ---- per-task JSON -------------------------------------------------- #
    t01 = json.loads((run_dir / "tasks" / "T01.json").read_text(encoding="utf-8"))
    assert t01["task_id"] == "T01"
    assert "SINAN" in t01["response_text"]
    # Bronze tasks are flagged for human review (no numerics/citations to check).
    assert t01["score"]["needs_human_review"] in (True, False)

    # ---- summary.csv ---------------------------------------------------- #
    csv_lines = (run_dir / "summary.csv").read_text(encoding="utf-8").splitlines()
    assert csv_lines[0].startswith("task_id,task_name,level")
    assert len(csv_lines) == 1 + 3

    # ---- leaderboard ---------------------------------------------------- #
    board = load_leaderboard(tmp_path)
    assert len(board) == 1
    assert board[0]["model"] == "scripted:demo"


def test_leaderboard_appends_across_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("EPIBENCH_NETWORK_SCORING", "0")
    backend = _ScriptedBackend("demo", "hello world")
    for _ in range(2):
        manifest = run_benchmark(all_tasks()[:1], backend)
        write_run(manifest, tmp_path)
    board = load_leaderboard(tmp_path)
    assert len(board) == 2


class _AuthFailingBackend(DummyBackend):
    def complete(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        raise RuntimeError("401 Unauthorized: invalid API key")


class _GenericFailingBackend(DummyBackend):
    def complete(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        raise RuntimeError("connection reset")


def test_runtime_openrouter_fallback_on_auth_error(tmp_path, monkeypatch):
    monkeypatch.setenv("EPIBENCH_NETWORK_SCORING", "0")
    monkeypatch.setenv("EPIBENCH_RESULTS_DIR", str(tmp_path))

    from epibench import runner as runner_mod

    fallback = _ScriptedBackend("fallback", "fallback response")
    monkeypatch.setattr(runner_mod, "fallback_backend_for", lambda _b, _s: fallback)

    backend = _AuthFailingBackend("failing")
    manifest = run_benchmark(all_tasks()[:1], backend)
    record = manifest.tasks[0]
    assert record.error is None
    assert record.response_text == "fallback response"
    assert any("OpenRouter fallback" in note for note in record.score.notes)


def test_no_fallback_on_non_auth_error(tmp_path, monkeypatch):
    monkeypatch.setenv("EPIBENCH_NETWORK_SCORING", "0")
    monkeypatch.setenv("EPIBENCH_RESULTS_DIR", str(tmp_path))

    from epibench import runner as runner_mod

    fallback = _ScriptedBackend("fallback", "should not be used")
    monkeypatch.setattr(runner_mod, "fallback_backend_for", lambda _b, _s: fallback)

    backend = _GenericFailingBackend("failing")
    manifest = run_benchmark(all_tasks()[:1], backend)
    record = manifest.tasks[0]
    assert record.error is not None
    assert "connection reset" in record.error
