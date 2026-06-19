"""Benchmark runner: orchestrates tasks → backend → score → persist."""

from __future__ import annotations

import logging
import time
import traceback
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from .config import Settings, load_settings
from .models.base import ModelBackend, ModelResponse, _is_auth_error, fallback_backend_for
from .scoring.auto import auto_score
from .scoring.reference import load_reference
from .scoring.rubric import CategoryScores, Penalty, score_task
from .storage import RunManifest, TaskRecord, write_run
from .tasks import Task

log = logging.getLogger("epibench.runner")


def _system_prompt() -> str:
    return (
        "You are being evaluated on EpiBench-1.0, a public-health & epidemiology "
        "agent benchmark. Answer the task as completely and precisely as possible. "
        "Where you compute epidemiological metrics, label each numeric result "
        "clearly (e.g. 'Incidence rate: 123.4'). Where you cite literature, give "
        "explicit PMIDs (e.g. 'PMID: 12345678'). Do not output individual-level "
        "or personally-identifiable data."
    )


ProgressCb = Callable[[int, int, Task], None]


def _complete_with_fallback(
    backend: ModelBackend,
    prompt: str,
    *,
    system: str | None,
    settings: Settings,
) -> tuple[ModelResponse, bool]:
    """Try the primary backend; on auth/key failure retry via OpenRouter.

    Returns the backend that produced the response and whether the fallback
    was used.
    """
    try:
        return backend.timed_complete(prompt, system=system), False
    except Exception as e:
        if not _is_auth_error(e):
            raise
        fb = fallback_backend_for(backend, settings)
        if fb is None:
            raise
        try:
            return fb.timed_complete(prompt, system=system), True
        except Exception as e2:  # pragma: no cover - exercised via mocked tests
            raise RuntimeError(
                f"Primary backend failed: {e}; OpenRouter fallback failed: {e2}"
            ) from e2


def run_task(
    task: Task,
    backend: ModelBackend,
    settings: Settings,
) -> TaskRecord:
    """Run one task end-to-end. Never raises — failures are recorded as `error`."""
    ref = load_reference(task.id, settings.reference_answers_dir)
    response_text = ""
    latency = 0.0
    token_usage: dict[str, int] = {}
    finish_reason: str | None = None
    error: str | None = None
    used_fallback = False

    try:
        resp, used_fallback = _complete_with_fallback(
            backend, task.prompt, system=_system_prompt(), settings=settings
        )
        response_text = resp.text
        latency = resp.latency_seconds
        token_usage = resp.token_usage
        finish_reason = resp.finish_reason
        if used_fallback:
            log.info("OpenRouter fallback succeeded for %s", task.id)
    except Exception as e:  # backend failures shouldn't abort the whole run
        error = f"{type(e).__name__}: {e}"
        log.warning("Backend failed on %s: %s", task.id, error)

    # Scoring ------------------------------------------------------------- #
    if error:
        notes = ["Backend error — could not produce a response to score."]
        breakdown = score_task(
            task.max_points,
            CategoryScores(),
            {},
            needs_human_review=True,
            notes=notes,
        )
        auto = None
    else:
        auto = auto_score(task, response_text, ref, settings)
        notes = list(auto.notes)
        if used_fallback:
            notes.insert(0, "OpenRouter fallback was used for this task.")
        breakdown = score_task(
            task.max_points,
            auto.category_scores,
            auto.penalties,
            needs_human_review=auto.needs_human_review,
            notes=notes,
        )

    return TaskRecord(
        task_id=task.id,
        task_name=task.name,
        level=task.level.value,
        domain=task.domain.value,
        max_points=task.max_points,
        prompt=task.prompt,
        response_text=response_text,
        latency_seconds=latency,
        token_usage=token_usage,
        finish_reason=finish_reason,
        score=breakdown,
        auto=auto,
        error=error,
    )


def run_benchmark(
    tasks: list[Task],
    backend: ModelBackend,
    *,
    settings: Settings | None = None,
    progress_cb: ProgressCb | None = None,
    fail_fast: bool = False,
) -> RunManifest:
    """Run a list of tasks against a backend, returning a populated manifest."""
    settings = settings or load_settings()
    run_id = datetime.now().strftime("%Y%m%dT%H%M%S")
    manifest = RunManifest(
        run_id=run_id,
        model=backend.display_name,
        created_at=datetime.now().isoformat(timespec="seconds"),
    )

    for i, task in enumerate(tasks, start=1):
        if progress_cb:
            progress_cb(i, len(tasks), task)
        try:
            record = run_task(task, backend, settings)
        except Exception:
            # run_task is meant to swallow errors; this is a last-resort guard.
            tb = traceback.format_exc()
            log.exception("Unexpected failure scoring %s", task.id)
            record = TaskRecord(
                task_id=task.id,
                task_name=task.name,
                level=task.level.value,
                domain=task.domain.value,
                max_points=task.max_points,
                prompt=task.prompt,
                response_text="",
                latency_seconds=0.0,
                token_usage={},
                finish_reason=None,
                score=score_task(
                    task.max_points,
                    CategoryScores(),
                    {Penalty.PRIVACY_VIOLATION: -20} if False else {},
                    needs_human_review=True,
                    notes=[f"Runner crash: {tb.splitlines()[-1]}"],
                ),
                error="runner crash",
            )
            if fail_fast:
                raise
        manifest.tasks.append(record)
        # Yield control briefly so log streams flush in long runs.
        time.sleep(0)

    return manifest


def save_run(manifest: RunManifest, results_dir: Path | str | None = None) -> Path:
    from .config import DEFAULT_RESULTS_DIR

    return write_run(manifest, Path(results_dir) if results_dir else DEFAULT_RESULTS_DIR)
