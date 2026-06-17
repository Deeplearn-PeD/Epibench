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
