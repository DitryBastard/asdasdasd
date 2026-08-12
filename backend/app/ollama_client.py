import httpx

from .config import settings


class OllamaClient:
    """Thin async client for a local Ollama server (chat + embeddings)."""

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        model = model or settings.ollama_chat_model
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        if not texts:
            return []
        model = model or settings.ollama_embed_model
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json={"model": model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()
            return data["embeddings"]

    async def health(self) -> dict:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return response.json()
