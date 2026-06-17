"""Google Gemini backend (google-genai SDK)."""

from __future__ import annotations

from ..config import Settings, load_settings
from .base import BackendError, ModelBackend, ModelResponse


class GeminiBackend(ModelBackend):
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        *,
        settings: Settings | None = None,
    ) -> None:
        self.model_name = model
        self.api_key = api_key
        self.display_name = f"gemini:{model}"
        self._settings = settings or load_settings()
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            from google import genai  # type: ignore[import-not-found]
        except ImportError as e:  # pragma: no cover - depends on env
            raise BackendError(
                "The 'google-genai' package is not installed. "
                "Install with: pip install epibench[gemini]"
            ) from e
        kwargs = {}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        self._client = genai.Client(**kwargs)
        return self._client

    def complete(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        client = self._ensure_client()
        kwargs: dict = {"model": self.model_name, "contents": prompt}
        if system:
            from google.genai import types  # type: ignore[import-not-found]

            kwargs["config"] = types.GenerateContentConfig(system_instruction=system)
        resp = client.models.generate_content(**kwargs)
        text = getattr(resp, "text", "") or ""
        usage = {}
        meta = getattr(resp, "usage_metadata", None)
        if meta is not None:
            usage = {
                "prompt_tokens": getattr(meta, "prompt_token_count", 0) or 0,
                "completion_tokens": getattr(meta, "candidates_token_count", 0) or 0,
                "total_tokens": getattr(meta, "total_token_count", 0) or 0,
            }
        return ModelResponse(
            text=text,
            raw={"model": self.model_name},
            token_usage=usage,
            finish_reason=None,
        )
