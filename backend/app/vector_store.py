import uuid

import chromadb
from chromadb.config import Settings as ChromaSettings

from .config import settings

COLLECTION_NAME = "translation_memory"


class VectorStore:
    """Persistent local vector store holding the translation memory.

    Embeddings are always supplied by the caller (via Ollama) - Chroma is
    used purely as a local, file-backed vector index, never as an embedding
    provider itself, so it needs no network access.
    """

    def __init__(self):
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_segments(self, items: list[dict]) -> list[str]:
        if not items:
            return []
        ids = [str(uuid.uuid4()) for _ in items]
        self._collection.add(
            ids=ids,
            embeddings=[item["embedding"] for item in items],
            documents=[item["source_text"] for item in items],
            metadatas=[
                {
                    "source_text": item["source_text"],
                    "target_text": item["target_text"],
                    "source_lang": item["source_lang"],
                    "target_lang": item["target_lang"],
                    "document_title": item.get("document_title") or "",
                    "created_at": item.get("created_at") or "",
                }
                for item in items
            ],
        )
        return ids

    def query(
        self,
        embedding: list[float],
        source_lang: str,
        target_lang: str,
        top_k: int,
    ) -> list[dict]:
        if self._collection.count() == 0:
            return []
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, self._collection.count()),
            where={"$and": [{"source_lang": source_lang}, {"target_lang": target_lang}]},
        )
        ids = result["ids"][0] if result["ids"] else []
        matches = []
        for i, item_id in enumerate(ids):
            similarity = 1.0 - result["distances"][0][i]
            matches.append({"id": item_id, "similarity": similarity, **result["metadatas"][0][i]})
        return matches

    def search_semantic(self, embedding: list[float], top_k: int) -> list[dict]:
        if self._collection.count() == 0:
            return []
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, self._collection.count()),
        )
        ids = result["ids"][0] if result["ids"] else []
        matches = []
        for i, item_id in enumerate(ids):
            similarity = 1.0 - result["distances"][0][i]
            matches.append({"id": item_id, "similarity": similarity, **result["metadatas"][0][i]})
        return matches

    def _where_for(self, source_lang: str | None, target_lang: str | None) -> dict | None:
        if source_lang and target_lang:
            return {"$and": [{"source_lang": source_lang}, {"target_lang": target_lang}]}
        if source_lang:
            return {"source_lang": source_lang}
        if target_lang:
            return {"target_lang": target_lang}
        return None

    def list_recent(
        self,
        source_lang: str | None,
        target_lang: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        items = self.list_all(source_lang, target_lang)
        return items[offset : offset + limit]

    def list_all(self, source_lang: str | None = None, target_lang: str | None = None) -> list[dict]:
        result = self._collection.get(where=self._where_for(source_lang, target_lang))
        items = [{"id": item_id, **result["metadatas"][i]} for i, item_id in enumerate(result["ids"])]
        items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return items

    def count(self, source_lang: str | None = None, target_lang: str | None = None) -> int:
        where = self._where_for(source_lang, target_lang)
        if where is None:
            return self._collection.count()
        result = self._collection.get(where=where)
        return len(result["ids"])

    def delete(self, item_id: str) -> None:
        self._collection.delete(ids=[item_id])


vector_store = VectorStore()
