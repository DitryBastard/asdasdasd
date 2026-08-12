from fastapi import APIRouter

from ..config import settings
from ..ollama_client import OllamaClient
from ..schemas import HealthResponse
from ..vector_store import vector_store

router = APIRouter(prefix="/api", tags=["health"])
ollama = OllamaClient()


@router.get("/health", response_model=HealthResponse)
async def health():
    try:
        await ollama.health()
        ollama_reachable = True
    except Exception:
        ollama_reachable = False
    return {
        "status": "ok",
        "ollama_reachable": ollama_reachable,
        "chat_model": settings.ollama_chat_model,
        "embed_model": settings.ollama_embed_model,
        "memory_count": vector_store.count(),
    }
