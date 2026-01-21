"""
Unit tests for embedding runtime configuration.

These tests avoid loading real embedding models (no downloads) by targeting:
- CPU thread/env configuration helpers
- Remote (OpenAI-compatible) embedding client logic (mocked HTTP)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import db  # noqa: E402


def test_configure_embedding_threads_cpu_forces_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMP_NUM_THREADS", "32")
    monkeypatch.delenv("REALITYCHECK_EMBED_THREADS", raising=False)
    monkeypatch.delenv("REALITYCHECK_EMBEDDING_THREADS", raising=False)
    monkeypatch.delenv("EMBEDDING_CPU_THREADS", raising=False)

    threads = db.configure_embedding_threads(device="cpu")

    assert threads == 4
    assert db.os.environ["OMP_NUM_THREADS"] == "4"


def test_configure_embedding_threads_cpu_respects_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMP_NUM_THREADS", "32")
    monkeypatch.setenv("REALITYCHECK_EMBED_THREADS", "8")
    monkeypatch.delenv("REALITYCHECK_EMBEDDING_THREADS", raising=False)
    monkeypatch.delenv("EMBEDDING_CPU_THREADS", raising=False)

    threads = db.configure_embedding_threads(device="cpu")

    assert threads == 8
    assert db.os.environ["OMP_NUM_THREADS"] == "8"


def test_configure_embedding_threads_non_cpu_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMP_NUM_THREADS", "32")
    monkeypatch.delenv("REALITYCHECK_EMBED_THREADS", raising=False)
    monkeypatch.delenv("REALITYCHECK_EMBEDDING_THREADS", raising=False)
    monkeypatch.delenv("EMBEDDING_CPU_THREADS", raising=False)

    threads = db.configure_embedding_threads(device="cuda:0")

    assert threads == 0
    assert db.os.environ["OMP_NUM_THREADS"] == "32"


def _mock_urlopen_json(payload: dict[str, Any]) -> MagicMock:
    resp = MagicMock()
    resp.__enter__.return_value = resp
    resp.read.return_value = json.dumps(payload).encode("utf-8")
    return resp


def test_openai_compat_embedder_encode_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    embedder = db.OpenAICompatEmbedder(
        model="test-model",
        api_base="http://example.test/v1",
        api_key="test-key",
    )

    mocked = _mock_urlopen_json(
        {
            "object": "list",
            "data": [
                {"index": 0, "object": "embedding", "embedding": [0.1, 0.2, 0.3]},
                {"index": 1, "object": "embedding", "embedding": [0.4, 0.5, 0.6]},
            ],
            "model": "test-model",
        }
    )

    with patch("urllib.request.urlopen", return_value=mocked):
        out = embedder.encode(["a", "b"])

    assert out == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


def test_get_embedder_uses_openai_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REALITYCHECK_EMBED_PROVIDER", "openai")
    monkeypatch.setenv("REALITYCHECK_EMBED_API_BASE", "http://example.test/v1")
    monkeypatch.setenv("REALITYCHECK_EMBED_API_KEY", "test-key")
    monkeypatch.setenv("REALITYCHECK_EMBED_MODEL", "test-model")

    db._embedder = None
    embedder = db.get_embedder()

    assert isinstance(embedder, db.OpenAICompatEmbedder)


def test_embed_text_raises_on_dim_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyEmbedder:
        def encode(self, text):
            return [0.1, 0.2]  # length 2

    monkeypatch.setattr(db, "EMBEDDING_DIM", 3)
    db._embedder = DummyEmbedder()

    with pytest.raises(ValueError, match="Embedding dim mismatch"):
        db.embed_text("hello")
