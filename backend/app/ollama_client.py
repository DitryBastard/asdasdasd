import httpx

from .config import settings


class OllamaError(RuntimeError):
    """Raised when Ollama is unreachable or returns an error response.

    Registered with a FastAPI exception handler (see main.py) so any of
    these become a clean 503 with an actionable message, instead of an
    unhandled 500 traceback.
    """


def _unreachable_message(base_url: str) -> str:
    return (
        f"Не удалось подключиться к Ollama по адресу {base_url}. "
        "Убедитесь, что она запущена (команда `ollama list` в терминале должна отвечать)."
    )


class OllamaClient:
    """Thin async client for a local Ollama server (chat + embeddings)."""

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")

    async def _post(self, path: str, payload: dict, timeout: float) -> dict:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(f"{self.base_url}{path}", json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.TransportError as exc:
            raise OllamaError(_unreachable_message(self.base_url)) from exc
        except httpx.HTTPStatusError as exc:
            model = payload.get("model", "")
            if exc.response.status_code == 404:
                raise OllamaError(
                    f'Модель "{model}" не найдена в Ollama. Выполните в терминале: ollama pull {model}'
                ) from exc
            raise OllamaError(
                f'Ollama вернула ошибку {exc.response.status_code} при обращении к модели "{model}".'
            ) from exc

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        model = model or settings.ollama_chat_model
        data = await self._post(
            "/api/chat",
            {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=180.0,
        )
        return data["message"]["content"]

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        if not texts:
            return []
        model = model or settings.ollama_embed_model
        data = await self._post("/api/embed", {"model": model, "input": texts}, timeout=120.0)
        return data["embeddings"]

    async def list_models(self) -> set[str]:
        """Names of models currently pulled in Ollama (used for health checks)."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
        except httpx.TransportError as exc:
            raise OllamaError(_unreachable_message(self.base_url)) from exc
        except httpx.HTTPStatusError as exc:
            raise OllamaError(f"Ollama вернула ошибку {exc.response.status_code}.") from exc
        return {m.get("name") or m.get("model") for m in data.get("models", [])}
