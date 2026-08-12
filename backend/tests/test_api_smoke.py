"""End-to-end wiring checks against the FastAPI app with Ollama mocked out.

These do not need a GPU or a running Ollama server: OllamaClient.embed/chat
are monkeypatched with small deterministic stand-ins, while Chroma (the
vector store) runs for real against a temp directory (see conftest.py). This
is what actually exercises the route <-> schema <-> service wiring, which
the pure-function unit tests elsewhere don't touch.
"""

import io
import re

from docx import Document
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.ollama_client import OllamaClient, OllamaError

KNOWN_TEXT = "Настройте параметр timeout перед запуском."

# Every distinct sentence embedded anywhere in this file needs its own
# mutually-orthogonal vector: the vector store is a session-wide singleton
# (see conftest.py), so data committed by one test is still there for later
# tests. Collapsing "any other sentence" onto one shared vector (as an
# earlier version of this file did) made unrelated sentences from different
# tests look like a 100% translation-memory match for each other once both
# had been embedded at least once - a real bug this exact fixture caught.
_KNOWN_SENTENCES = [
    KNOWN_TEXT,
    "Это новое предложение без совпадений.",
    "Первый абзац.",
    "Второй абзац.",
    "First paragraph.",
    "Second paragraph.",
    "Совсем новое предложение без совпадений в базе.",
    "Заголовок документа.",
    "Описание раздела.",
]


def _one_hot(text: str) -> list[float]:
    dims = len(_KNOWN_SENTENCES) + 1
    vector = [0.0] * dims
    vector[_KNOWN_SENTENCES.index(text) if text in _KNOWN_SENTENCES else -1] = 1.0
    return vector


async def fake_embed(self, texts, model=None):
    return [_one_hot(t) for t in texts]


async def fake_chat(self, messages, model=None, temperature=0.2):
    user_content = messages[-1]["content"]
    count = len(re.findall(r"^\d+\.", user_content, re.MULTILINE))
    return "\n".join(f"{i + 1}. [translated {i + 1}]" for i in range(count))


async def fake_chat_model_missing(self, messages, model=None, temperature=0.2):
    model = model or settings.ollama_chat_model
    raise OllamaError(f'Модель "{model}" не найдена в Ollama. Выполните в терминале: ollama pull {model}')


async def fake_list_models_all_present(self):
    return {settings.ollama_chat_model, settings.ollama_embed_model}


async def fake_list_models_missing_chat(self):
    return {settings.ollama_embed_model}


async def fake_list_models_unreachable(self):
    raise OllamaError("boom: connection refused")


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
        # Real assertion on content, not just count: proves the embedding-based
        # aligner (app/alignment.py) actually paired each source paragraph with
        # its matching translation rather than just zipping by position.
        assert preview["pairs"] == [
            {"source_text": "Первый абзац.", "target_text": "First paragraph."},
            {"source_text": "Второй абзац.", "target_text": "Second paragraph."},
        ]

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


def test_health_endpoint_when_models_present(monkeypatch):
    monkeypatch.setattr(OllamaClient, "list_models", fake_list_models_all_present)

    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["ollama_reachable"] is True
        assert body["chat_model_available"] is True
        assert body["embed_model_available"] is True


def test_health_endpoint_flags_missing_model(monkeypatch):
    monkeypatch.setattr(OllamaClient, "list_models", fake_list_models_missing_chat)

    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["ollama_reachable"] is True
        assert body["chat_model_available"] is False
        assert body["embed_model_available"] is True


def test_health_endpoint_when_ollama_unreachable(monkeypatch):
    monkeypatch.setattr(OllamaClient, "list_models", fake_list_models_unreachable)

    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["ollama_reachable"] is False
        assert body["chat_model_available"] is False


def test_translate_returns_503_with_actionable_message_when_model_missing(monkeypatch):
    monkeypatch.setattr(OllamaClient, "embed", fake_embed)
    monkeypatch.setattr(OllamaClient, "chat", fake_chat_model_missing)

    with TestClient(app) as client:
        response = client.post(
            "/api/translate",
            json={
                "text": "Совсем новое предложение без совпадений в базе.",
                "source_lang": "ru",
                "target_lang": "en",
            },
        )
        assert response.status_code == 503
        assert "ollama pull" in response.json()["detail"]


def test_translate_document_formatted_returns_docx_with_translated_text(monkeypatch):
    monkeypatch.setattr(OllamaClient, "embed", fake_embed)
    monkeypatch.setattr(OllamaClient, "chat", fake_chat)

    document = Document()
    document.add_paragraph("Заголовок документа.")
    document.add_paragraph("Описание раздела.")
    buffer = io.BytesIO()
    document.save(buffer)

    with TestClient(app) as client:
        response = client.post(
            "/api/translate/document/formatted",
            files={
                "file": (
                    "исходник.docx",
                    buffer.getvalue(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            data={"source_lang": "ru", "target_lang": "en"},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert "filename*=UTF-8''" in response.headers["content-disposition"]

    rebuilt = Document(io.BytesIO(response.content))
    texts = [p.text for p in rebuilt.paragraphs if p.text.strip()]
    assert texts == ["[translated 1]", "[translated 2]"]


def test_translate_document_formatted_rejects_non_docx(monkeypatch):
    monkeypatch.setattr(OllamaClient, "embed", fake_embed)

    with TestClient(app) as client:
        response = client.post(
            "/api/translate/document/formatted",
            files={"file": ("notes.txt", b"Some text.", "text/plain")},
            data={"source_lang": "ru", "target_lang": "en"},
        )

    assert response.status_code == 400
