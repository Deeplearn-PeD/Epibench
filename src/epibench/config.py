"""Runtime configuration: API keys, default directories, network settings.

All settings are read from environment variables with sensible defaults so the
runner works out-of-the-box against local backends and defers to env-provided
credentials for hosted providers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Repo-relative paths.
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
REFERENCE_ANSWERS_DIR = PROJECT_ROOT / "data" / "reference_answers"
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results"


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_base_url: str | None
    anthropic_api_key: str | None
    gemini_api_key: str | None
    openrouter_api_key: str | None
    results_dir: Path
    reference_answers_dir: Path
    # NCBI E-utilities (PMID verification) — polite usage requires an email/tool.
    ncbi_email: str | None
    ncbi_tool: str
    ncbi_api_key: str | None
    # Hard ceiling for any single network call during scoring (seconds).
    http_timeout: float
    # Fail scoring network calls silently (return "unknown") instead of raising.
    allow_network_scoring: bool

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Settings:
        env = env or dict(os.environ)
        return cls(
            openai_api_key=env.get("OPENAI_API_KEY"),
            openai_base_url=env.get("OPENAI_BASE_URL"),
            anthropic_api_key=env.get("ANTHROPIC_API_KEY"),
            gemini_api_key=env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY"),
            openrouter_api_key=env.get("OPENROUTER_API_KEY"),
            results_dir=Path(env.get("EPIBENCH_RESULTS_DIR", DEFAULT_RESULTS_DIR)),
            reference_answers_dir=Path(
                env.get("EPIBENCH_REFERENCE_DIR", REFERENCE_ANSWERS_DIR)
            ),
            ncbi_email=env.get("NCBI_EMAIL"),
            ncbi_tool=env.get("NCBI_TOOL", "epibench"),
            ncbi_api_key=env.get("NCBI_API_KEY"),
            http_timeout=float(env.get("EPIBENCH_HTTP_TIMEOUT", "15")),
            allow_network_scoring=env.get("EPIBENCH_NETWORK_SCORING", "1") == "1",
        )


def load_settings() -> Settings:
    return Settings.from_env()
