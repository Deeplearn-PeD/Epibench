"""Abstract model backend and the spec-string factory.

A `ModelBackend` is a thin, provider-agnostic adapter that turns a prompt into a
normalized `ModelResponse`. The simple-chat implementation here is the baseline;
a future tool-use/agent loop can subclass or wrap these same backends without
changing the runner contract.
"""

from __future__ import annotations

import sys
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


# --------------------------------------------------------------------------- #
# OpenRouter fallback helpers
# --------------------------------------------------------------------------- #


def _is_auth_error(exc: Exception) -> bool:
    """Best-effort detection of authentication / API-key failures.

    Catches typed errors from the major SDKs when they are installed, plus a
    message heuristic for unknown or lightweight clients.
    """
    exc_type = type(exc)
    for module_name, attr_name in (
        ("openai", "AuthenticationError"),
        ("anthropic", "AuthenticationError"),
        ("google.api_core.exceptions", "PermissionDenied"),
        ("google.api_core.exceptions", "Unauthorized"),
    ):
        mod = sys.modules.get(module_name)
        if mod is None:
            try:
                mod = __import__(module_name, fromlist=[attr_name])
            except Exception:  # pragma: no cover - optional dependency
                continue
        known = getattr(mod, attr_name, None)
        if known is not None and isinstance(exc, known):
            return True

    name = exc_type.__name__.lower()
    if any(term in name for term in ("auth", "unauthorized", "permission", "forbidden")):
        return True

    msg = str(exc).lower()
    return any(
        term in msg
        for term in (
            "api key",
            "apikey",
            "unauthorized",
            "401",
            "403",
            "invalid token",
            "token expired",
            "expired",
            "authentication",
            "permission denied",
            "access denied",
        )
    )


def _openrouter_fallback_id(display_name: str) -> str | None:
    """Map a primary backend display name to the OpenRouter model id, if known."""
    if display_name.startswith("openai:"):
        model = display_name[len("openai:") :]
        if not model or "/" in model:
            # Local/custom OpenAI-compatible endpoints are not mirrored here.
            return None
        return f"openai/{model}"
    if display_name.startswith("anthropic:"):
        model = display_name[len("anthropic:") :]
        if not model:
            return None
        return f"anthropic/{model}"
    if display_name.startswith("gemini:"):
        model = display_name[len("gemini:") :]
        if not model:
            return None
        return f"google/{model}"
    return None


def fallback_backend_for(backend: ModelBackend, settings: Any) -> ModelBackend | None:
    """Return an OpenRouter substitute for `backend`, or None if not possible."""
    from ..config import Settings

    if not isinstance(settings, Settings):
        raise TypeError("settings must be a Settings instance")
    if not settings.openrouter_api_key:
        return None
    or_id = _openrouter_fallback_id(backend.display_name)
    if not or_id:
        return None
    return _make_openrouter(or_id)


# --------------------------------------------------------------------------- #


def make_backend(spec: str) -> ModelBackend:
    """Build a backend from a `provider:model` (or `provider:base_url:model`) spec.

    Supported spec shapes:
      openai:<model>                          e.g. openai:gpt-4o
      openai:<base_url>:<model>               any OpenAI-compatible endpoint
      openai:<base_url>::<model>              same, but model may contain ':'
      openrouter:<model>                      e.g. openrouter:anthropic/claude-3.5-sonnet
      anthropic:<model>                       e.g. anthropic:claude-sonnet-4-5
      gemini:<model>                          e.g. gemini:gemini-2.0-flash
      dummy:<anything>                        offline echo backend (tests/demo)
    """
    spec = spec.strip()
    if ":" not in spec:
        raise BackendError(
            f"Invalid model spec {spec!r}. Expected 'provider:model' (e.g. 'openai:gpt-4o')."
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
        f"Unknown provider {provider!r}. Use one of: openai, openrouter, anthropic, gemini, dummy."
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

    # If no OpenAI key is available but OpenRouter is configured, mirror the
    # request through OpenRouter (e.g. openai:gpt-4o -> openrouter:openai/gpt-4o).
    if not base_url and not settings.openai_api_key and settings.openrouter_api_key:
        or_id = _openrouter_fallback_id(f"openai:{model}")
        if or_id:
            return _make_openrouter(or_id)

    return OpenAIBackend(
        model=model,
        api_key=settings.openai_api_key,
        base_url=base_url or settings.openai_base_url,
    )


def _split_url_and_model(rest: str) -> tuple[str, str]:
    """Split 'https://host:port/v1:model' into ('https://host:port/v1', 'model').

    Model names that contain ':' (e.g. Ollama tags like 'qwen3.5:4b') can be
    preserved by using a double-colon separator:
    'https://host:port/v1::model:tag'.
    """
    # Explicit separator: everything before '::' is the base URL, after is the model.
    if "::" in rest:
        base, _, model = rest.partition("::")
        return base, model

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
        raise BackendError("OPENROUTER_API_KEY is not set. Set it to use openrouter: models.")
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
    if not settings.anthropic_api_key and settings.openrouter_api_key:
        or_id = _openrouter_fallback_id(f"anthropic:{model}")
        if or_id:
            return _make_openrouter(or_id)
    return AnthropicBackend(model=model, api_key=settings.anthropic_api_key)


def _make_gemini(model: str) -> ModelBackend:
    from ..config import load_settings
    from .gemini_backend import GeminiBackend

    settings = load_settings()
    if not settings.gemini_api_key and settings.openrouter_api_key:
        or_id = _openrouter_fallback_id(f"gemini:{model}")
        if or_id:
            return _make_openrouter(or_id)
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
