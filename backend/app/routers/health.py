from fastapi import APIRouter

from ..config import settings
from ..ollama_client import OllamaClient
from ..schemas import HealthResponse
from ..vector_store import vector_store

router = APIRouter(prefix="/api", tags=["health"])
ollama = OllamaClient()


@router.get("/health", response_model=HealthResponse)
async def health():
    ollama_reachable = False
    chat_model_available = False
    embed_model_available = False
    try:
        available = await ollama.list_models()
        ollama_reachable = True
        chat_model_available = settings.ollama_chat_model in available
        embed_model_available = settings.ollama_embed_model in available
    except Exception:
        pass
    return {
        "status": "ok",
        "ollama_reachable": ollama_reachable,
        "chat_model": settings.ollama_chat_model,
        "embed_model": settings.ollama_embed_model,
        "chat_model_available": chat_model_available,
        "embed_model_available": embed_model_available,
        "memory_count": vector_store.count(),
    }
