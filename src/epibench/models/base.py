"""Abstract model backend and the spec-string factory.

A `ModelBackend` is a thin, provider-agnostic adapter that turns a prompt into a
normalized `ModelResponse`. The simple-chat implementation here is the baseline;
a future tool-use/agent loop can subclass or wrap these same backends without
changing the runner contract.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelResponse:
    text: str
    raw: dict[str, Any] = field(default_factory=dict)
    token_usage: dict[str, int] = field(default_factory=dict)
    latency_seconds: float = 0.0
    finish_reason: str | None = None


class ModelBackend:
    """Base class. Subclasses implement `complete`."""

    display_name: str

    def complete(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        raise NotImplementedError

    def timed_complete(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        start = time.perf_counter()
        resp = self.complete(prompt, system=system)
        resp.latency_seconds = resp.latency_seconds or (time.perf_counter() - start)
        return resp


class BackendError(RuntimeError):
    """Raised when a backend cannot be constructed or fails irrecoverably."""


def make_backend(spec: str) -> ModelBackend:
    """Build a backend from a `provider:model` (or `provider:base_url:model`) spec.

    Supported spec shapes:
      openai:<model>                          e.g. openai:gpt-4o
      openai:<base_url>:<model>               any OpenAI-compatible endpoint
      openrouter:<model>                      e.g. openrouter:anthropic/claude-3.5-sonnet
      anthropic:<model>                       e.g. anthropic:claude-sonnet-4-5
      gemini:<model>                          e.g. gemini:gemini-2.0-flash
      dummy:<anything>                        offline echo backend (tests/demo)
    """
    spec = spec.strip()
    if ":" not in spec:
        raise BackendError(
            f"Invalid model spec {spec!r}. Expected 'provider:model' "
            "(e.g. 'openai:gpt-4o')."
        )
    provider, _, rest = spec.partition(":")
    provider = provider.lower()
    rest = rest.strip()
    if not rest:
        raise BackendError(f"Empty model name in spec {spec!r}")

    if provider == "openai":
        return _make_openai(rest, base_url=None)
    if provider == "openrouter":
        return _make_openrouter(rest)
    if provider == "anthropic":
        return _make_anthropic(rest)
    if provider == "gemini":
        return _make_gemini(rest)
    if provider == "dummy":
        return DummyBackend(rest)

    raise BackendError(
        f"Unknown provider {provider!r}. Use one of: openai, openrouter, "
        "anthropic, gemini, dummy."
    )


def _make_openai(rest: str, base_url: str | None) -> ModelBackend:
    # `rest` is either "<model>" or "<base_url>:<model>" where base_url starts
    # with http(s)://. The model name never contains ':' or '/'.
    if rest.startswith(("http://", "https://")):
        base_url, model = _split_url_and_model(rest)
        if not model:
            raise BackendError(
                f"Could not parse model name from spec {rest!r}. "
                "Use 'openai:<base_url>:<model>' for custom endpoints "
                "(e.g. 'openai:http://localhost:11434/v1:llama3')."
            )
    else:
        base_url, model = None, rest

    from ..config import load_settings
    from .openai_backend import OpenAIBackend

    settings = load_settings()
    return OpenAIBackend(
        model=model,
        api_key=settings.openai_api_key,
        base_url=base_url or settings.openai_base_url,
    )


def _split_url_and_model(rest: str) -> tuple[str, str]:
    """Split 'https://host:port/v1:model' into ('https://host:port/v1', 'model')."""
    scheme, sep, after = rest.partition("://")
    if not sep:
        return "", rest
    # The model is everything after the last ':' that's not part of host:port.
    # We split from the right; the model token never contains '/'.
    last_colon = after.rfind(":")
    if last_colon == -1:
        return rest, ""
    base = after[:last_colon]
    model = after[last_colon + 1 :]
    # If the segment after the last ':' contains '/', it's part of the URL path.
    if "/" in model:
        return rest, ""
    return f"{scheme}://{base}", model


def _make_openrouter(model: str) -> ModelBackend:
    from ..config import load_settings
    from .openai_backend import OpenAIBackend

    settings = load_settings()
    if not settings.openrouter_api_key:
        raise BackendError(
            "OPENROUTER_API_KEY is not set. Set it to use openrouter: models."
        )
    return OpenAIBackend(
        model=model,
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        display_name=f"openrouter:{model}",
    )


def _make_anthropic(model: str) -> ModelBackend:
    from ..config import load_settings
    from .anthropic_backend import AnthropicBackend

    settings = load_settings()
    return AnthropicBackend(model=model, api_key=settings.anthropic_api_key)


def _make_gemini(model: str) -> ModelBackend:
    from ..config import load_settings
    from .gemini_backend import GeminiBackend

    settings = load_settings()
    return GeminiBackend(model=model, api_key=settings.gemini_api_key)


class DummyBackend(ModelBackend):
    """Offline echo backend. Useful for demos and tests (no API key needed)."""

    def __init__(self, model: str) -> None:
        self.model_name = model
        self.display_name = f"dummy:{model}"

    def complete(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        echo = f"[dummy:{self.model_name}] {prompt[:200]}"
        return ModelResponse(
            text=echo,
            raw={"echoed": True},
            token_usage={"prompt_tokens": len(prompt.split()), "completion_tokens": 0},
            latency_seconds=0.0,
            finish_reason="dummy",
        )
