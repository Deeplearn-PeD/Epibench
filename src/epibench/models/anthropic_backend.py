"""Anthropic Claude backend."""

from __future__ import annotations

from ..config import Settings, load_settings
from .base import BackendError, ModelBackend, ModelResponse


class AnthropicBackend(ModelBackend):
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        *,
        settings: Settings | None = None,
    ) -> None:
        self.model_name = model
        self.api_key = api_key
        self.display_name = f"anthropic:{model}"
        self._settings = settings or load_settings()
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            import anthropic  # type: ignore[import-not-found]
        except ImportError as e:  # pragma: no cover - depends on env
            raise BackendError(
                "The 'anthropic' package is not installed. "
                "Install with: pip install epibench[anthropic]"
            ) from e
        kwargs = {}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        self._client = anthropic.Anthropic(**kwargs)
        return self._client

    def complete(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        client = self._ensure_client()
        kwargs: dict = {"model": self.model_name, "max_tokens": 8192, "messages": [
            {"role": "user", "content": prompt}
        ]}
        if system:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        text = "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )
        usage = {
            "prompt_tokens": resp.usage.input_tokens,
            "completion_tokens": resp.usage.output_tokens,
            "total_tokens": resp.usage.input_tokens + resp.usage.output_tokens,
        }
        return ModelResponse(
            text=text,
            raw={"id": resp.id, "stop_reason": resp.stop_reason},
            token_usage=usage,
            finish_reason=resp.stop_reason,
        )
