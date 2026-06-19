from __future__ import annotations

from epibench.models.base import BackendError, DummyBackend, make_backend
from epibench.models.openai_backend import OpenAIBackend


def test_dummy_backend_spec():
    backend = make_backend("dummy:demo-model")
    assert isinstance(backend, DummyBackend)
    assert backend.display_name == "dummy:demo-model"
    resp = backend.complete("hello")
    assert "hello" in resp.text
    assert resp.finish_reason == "dummy"


def test_invalid_spec_no_colon():
    import pytest

    with pytest.raises(BackendError):
        make_backend("gpt-4o")


def test_invalid_spec_empty_model():
    import pytest

    with pytest.raises(BackendError):
        make_backend("openai:")


def test_unknown_provider():
    import pytest

    with pytest.raises(BackendError):
        make_backend("acme:foo")


def test_openai_simple_spec_parses_model():
    # Build manually to avoid needing a real client; verify the parsing path.
    backend = OpenAIBackend(model="gpt-4o", api_key="sk-test", base_url=None)
    assert backend.model_name == "gpt-4o"
    assert backend.base_url is None


def test_openrouter_spec_requires_key(monkeypatch):
    import pytest

    # No OPENROUTER_API_KEY set → should error cleanly.
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(BackendError):
        make_backend("openrouter:anthropic/claude-3.5-sonnet")


def test_openai_url_plus_model_parsing(tmp_path, monkeypatch):
    # Directly exercise the URL splitter helper.
    from epibench.models.base import _split_url_and_model

    base, model = _split_url_and_model("http://localhost:11434/v1:llama3")
    assert base == "http://localhost:11434/v1"
    assert model == "llama3"


def test_openai_url_plus_model_with_colon_in_model(tmp_path, monkeypatch):
    # Ollama model names can include tags like "qwen3.5:4b".
    from epibench.models.base import _split_url_and_model

    base, model = _split_url_and_model("http://localhost:11434/v1::qwen3.5:4b")
    assert base == "http://localhost:11434/v1"
    assert model == "qwen3.5:4b"


def test_openrouter_fallback_id_mapping():
    from epibench.models.base import _openrouter_fallback_id

    assert _openrouter_fallback_id("openai:gpt-4o") == "openai/gpt-4o"
    assert _openrouter_fallback_id("anthropic:claude-sonnet-4-5") == "anthropic/claude-sonnet-4-5"
    assert _openrouter_fallback_id("gemini:gemini-2.0-flash") == "google/gemini-2.0-flash"
    # Local/custom endpoints and unknown providers have no mapping.
    assert _openrouter_fallback_id("openai:http://localhost:11434/v1:llama3") is None
    assert _openrouter_fallback_id("openrouter:anthropic/claude-3.5-sonnet") is None
    assert _openrouter_fallback_id("dummy:demo") is None


def test_missing_openai_key_falls_back_to_openrouter(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    backend = make_backend("openai:gpt-4o")
    assert backend.display_name == "openrouter:openai/gpt-4o"
    assert backend.model_name == "openai/gpt-4o"


def test_missing_anthropic_key_falls_back_to_openrouter(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    backend = make_backend("anthropic:claude-sonnet-4-5")
    assert backend.display_name == "openrouter:anthropic/claude-sonnet-4-5"


def test_missing_gemini_key_falls_back_to_openrouter(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    backend = make_backend("gemini:gemini-2.0-flash")
    assert backend.display_name == "openrouter:google/gemini-2.0-flash"


def test_no_fallback_when_provider_key_is_present(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    backend = make_backend("openai:gpt-4o")
    assert backend.display_name == "openai:gpt-4o"
