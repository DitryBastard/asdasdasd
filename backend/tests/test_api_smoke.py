"""End-to-end wiring checks against the FastAPI app with Ollama mocked out.

These do not need a GPU or a running Ollama server: OllamaClient.embed/chat
are monkeypatched with small deterministic stand-ins, while Chroma (the
vector store) runs for real against a temp directory (see conftest.py). This
is what actually exercises the route <-> schema <-> service wiring, which
the pure-function unit tests elsewhere don't touch.
"""

import re

from fastapi.testclient import TestClient

from app.main import app
from app.ollama_client import OllamaClient

KNOWN_TEXT = "Настройте параметр timeout перед запуском."
KNOWN_VECTOR = [1.0, 0.0, 0.0, 0.0]
DEFAULT_VECTOR = [0.0, 1.0, 0.0, 0.0]


async def fake_embed(self, texts, model=None):
    return [KNOWN_VECTOR if t == KNOWN_TEXT else DEFAULT_VECTOR for t in texts]


async def fake_chat(self, messages, model=None, temperature=0.2):
    user_content = messages[-1]["content"]
    count = len(re.findall(r"^\d+\.", user_content, re.MULTILINE))
    return "\n".join(f"{i + 1}. [translated {i + 1}]" for i in range(count))


async def fake_health(self):
    return {"models": []}


def test_translate_reuses_exact_memory_match(monkeypatch):
    monkeypatch.setattr(OllamaClient, "embed", fake_embed)
    monkeypatch.setattr(OllamaClient, "chat", fake_chat)

    with TestClient(app) as client:
        add_response = client.post(
            "/api/memory/entry",
            json={
                "source_text": KNOWN_TEXT,
                "target_text": "Configure the timeout parameter before starting.",
                "source_lang": "ru",
                "target_lang": "en",
                "document_title": "smoke-test",
            },
        )
        assert add_response.status_code == 200

        translate_response = client.post(
            "/api/translate",
            json={
                "text": f"{KNOWN_TEXT} Это новое предложение без совпадений.",
                "source_lang": "ru",
                "target_lang": "en",
            },
        )
        assert translate_response.status_code == 200
        body = translate_response.json()
        assert len(body["segments"]) == 2

        exact_segment = body["segments"][0]
        assert exact_segment["match"]["type"] == "exact"
        assert exact_segment["translation"] == "Configure the timeout parameter before starting."

        fresh_segment = body["segments"][1]
        assert fresh_segment["match"] is None
        assert fresh_segment["translation"] == "[translated 1]"


def test_document_pair_preview_and_commit(monkeypatch):
    monkeypatch.setattr(OllamaClient, "embed", fake_embed)

    with TestClient(app) as client:
        preview_response = client.post(
            "/api/memory/documents/preview",
            files={
                "source_file": ("source.txt", "Первый абзац.\n\nВторой абзац.", "text/plain"),
                "target_file": ("target.txt", "First paragraph.\n\nSecond paragraph.", "text/plain"),
            },
        )
        assert preview_response.status_code == 200
        preview = preview_response.json()
        assert len(preview["pairs"]) == 2

        commit_response = client.post(
            "/api/memory/documents/commit",
            json={
                "pairs": preview["pairs"],
                "source_lang": "ru",
                "target_lang": "en",
                "document_title": "smoke-doc",
            },
        )
        assert commit_response.status_code == 200
        assert commit_response.json()["added_segments"] >= 2


def test_health_endpoint(monkeypatch):
    monkeypatch.setattr(OllamaClient, "health", fake_health)

    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["ollama_reachable"] is True
        assert "chat_model" in body
