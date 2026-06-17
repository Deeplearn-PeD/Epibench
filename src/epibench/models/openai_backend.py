"""OpenAI backend. Also serves any OpenAI-compatible endpoint (Ollama, vLLM,
LM Studio, OpenRouter) via `base_url`.
"""

from __future__ import annotations

from ..config import Settings, load_settings
from .base import BackendError, ModelBackend, ModelResponse


class OpenAIBackend(ModelBackend):
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        display_name: str | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.model_name = model
        self.api_key = api_key
        self.base_url = base_url
        self.display_name = display_name or (
            f"openai:{base_url}:{model}" if base_url else f"openai:{model}"
        )
        self._settings = settings or load_settings()
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI  # type: ignore[import-not-found]
        except ImportError as e:  # pragma: no cover - depends on env
            raise BackendError(
                "The 'openai' package is not installed. "
                "Install with: pip install epibench[openai]"
            ) from e
        kwargs: dict = {}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["base_url"] = self.base_url
        self._client = OpenAI(**kwargs)
        return self._client

    def complete(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        client = self._ensure_client()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(model=self.model_name, messages=messages)
        choice = resp.choices[0]
        usage = {}
        if getattr(resp, "usage", None):
            usage = {
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
                "total_tokens": resp.usage.total_tokens,
            }
        return ModelResponse(
            text=choice.message.content or "",
            raw={"id": getattr(resp, "id", None)},
            token_usage=usage,
            finish_reason=choice.finish_reason,
        )
