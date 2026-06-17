"""EpiBench command-line interface.

Commands:
    run          Run one or more benchmark tasks against a model backend.
    list-tasks   Enumerate the 21 EpiBench tasks.
    compare      Show the cumulative leaderboard.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import load_settings
from .models.base import make_backend
from .runner import run_benchmark, save_run
from .storage import load_leaderboard
from .tasks import all_tasks, parse_task_selector

app = typer.Typer(
    name="epibench",
    add_completion=False,
    no_args_is_help=True,
    help="Run the EpiBench-1.0 public-health & epidemiology AI benchmark.",
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"epibench {__version__}")
        raise typer.Exit()


@app.callback()
def _main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    pass


@app.command("list-tasks")
def list_tasks(
    level: str | None = typer.Option(None, "--level", help="Filter by level."),
) -> None:
    """List all (or filtered) EpiBench tasks."""
    tasks = all_tasks()
    if level:
        tasks = [t for t in tasks if t.level.value.lower() == level.lower()]

    table = Table(title=f"EpiBench-1.0 tasks ({len(tasks)} shown)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Level")
    table.add_column("Domain")
    table.add_column("Competencies")
    table.add_column("Max", justify="right")
    for t in tasks:
        table.add_row(
            t.id,
            t.name,
            t.level.value,
            t.domain.value,
            ",".join(c.value for c in t.competencies),
            str(t.max_points),
        )
    console.print(table)
    console.print(
        f"Total max points: [b]{sum(t.max_points for t in tasks)}[/b]"
        + (" (full benchmark: 540)" if tasks == all_tasks() else "")
    )


@app.command("run")
def run(
    model: str = typer.Option(..., "--model", "-m", help="Model spec, e.g. openai:gpt-4o"),
    tasks: str = typer.Option(
        "all", "--tasks", "-t", help="Selector: 'all', 'T01,T03', 'bronze,silver'"
    ),
    results_dir: Path | None = typer.Option(
        None, "--results-dir", help="Override results directory."
    ),
    fail_fast: bool = typer.Option(False, "--fail-fast", help="Abort on first error."),
) -> None:
    """Run benchmark tasks against a model and persist scores."""
    try:
        task_list = parse_task_selector(tasks)
    except (KeyError, ValueError) as e:
        console.print(f"[red]Invalid --tasks selector:[/red] {e}")
        raise typer.Exit(code=2) from e

    console.print(f"[bold]EpiBench-1.0[/bold] — model [cyan]{model}[/cyan]")
    console.print(f"Running {len(task_list)} task(s): {', '.join(t.id for t in task_list)}")

    try:
        backend = make_backend(model)
    except Exception as e:
        console.print(f"[red]Could not build backend:[/red] {e}")
        raise typer.Exit(code=2) from e

    def progress(i: int, total: int, task) -> None:
        console.print(f"  [{i}/{total}] {task.id} {task.name} ({task.level.value}) ...", end=" ")

    manifest = run_benchmark(
        task_list,
        backend,
        progress_cb=progress,
        fail_fast=fail_fast,
    )

    run_dir = save_run(manifest, results_dir or load_settings().results_dir)

    pct = (
        round(100.0 * manifest.total_score / manifest.max_possible, 2)
        if manifest.max_possible
        else 0.0
    )
    console.print()
    console.print(f"[green]Done.[/green] Run saved to: [cyan]{run_dir}[/cyan]")
    console.print(
        f"Total score: [bold]{manifest.total_score}/{manifest.max_possible}[/bold] "
        f"({pct}%) — tier [bold yellow]{manifest.tier}[/bold yellow]"
    )
    if manifest.privacy_violation:
        console.print("[red bold]DISQUALIFIED: privacy violation detected.[/red bold]")


@app.command("compare")
def compare(
    results_dir: Path | None = typer.Option(
        None, "--results-dir", help="Override results directory."
    ),
) -> None:
    """Show the cumulative leaderboard."""
    directory = results_dir or load_settings().results_dir
    entries = load_leaderboard(directory)
    if not entries:
        console.print(f"No runs found under [cyan]{directory}[/cyan].")
        return

    entries_sorted = sorted(entries, key=lambda e: e.get("total_score", 0), reverse=True)
    table = Table(title="EpiBench-1.0 leaderboard")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Model")
    table.add_column("Score", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("%", justify="right")
    table.add_column("Tier")
    table.add_column("Run ID")
    for idx, e in enumerate(entries_sorted, 1):
        table.add_row(
            str(idx),
            str(e.get("model", "")),
            str(e.get("total_score", "")),
            str(e.get("max_possible", "")),
            str(e.get("percentage", "")),
            str(e.get("tier", "")),
            str(e.get("run_id", "")),
        )
    console.print(table)


if __name__ == "__main__":
    app()
