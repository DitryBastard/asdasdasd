from datetime import datetime, timezone

from .ollama_client import OllamaClient
from .segmentation import split_sentences
from .vector_store import vector_store

ollama = OllamaClient()


def preview_document_pair(source_paragraphs: list[str], target_paragraphs: list[str]) -> dict:
    """Naive positional alignment: pair up paragraph N of the source document
    with paragraph N of the translated document. This assumes the translated
    document keeps the same paragraph structure as the original, which holds
    for most bilingual technical documentation but is not guaranteed - the
    caller reviews and edits the pairs before they are committed.
    """
    pair_count = min(len(source_paragraphs), len(target_paragraphs))
    pairs = [
        {"source_text": source_paragraphs[i], "target_text": target_paragraphs[i]} for i in range(pair_count)
    ]
    return {
        "pairs": pairs,
        "source_paragraph_count": len(source_paragraphs),
        "target_paragraph_count": len(target_paragraphs),
    }


async def ingest_pairs(
    pairs: list[dict],
    source_lang: str,
    target_lang: str,
    document_title: str,
) -> int:
    """Store paragraph pairs in the translation memory, splitting each pair
    down to sentence level when both sides segment into the same number of
    sentences (giving finer-grained, more useful matches later). When the
    sentence counts disagree - e.g. the translator merged or split sentences -
    the paragraph is stored as a single unit instead of guessing an alignment.
    """
    units: list[tuple[str, str]] = []
    for pair in pairs:
        source_paragraph = pair["source_text"].strip()
        target_paragraph = pair["target_text"].strip()
        if not source_paragraph or not target_paragraph:
            continue
        source_sentences = split_sentences(source_paragraph, source_lang)
        target_sentences = split_sentences(target_paragraph, target_lang)
        if source_sentences and len(source_sentences) == len(target_sentences):
            units.extend(zip(source_sentences, target_sentences))
        else:
            units.append((source_paragraph, target_paragraph))

    if not units:
        return 0

    embeddings = await ollama.embed([source for source, _ in units])
    created_at = datetime.now(timezone.utc).isoformat()
    items = [
        {
            "source_text": source,
            "target_text": target,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "document_title": document_title,
            "created_at": created_at,
            "embedding": embedding,
        }
        for (source, target), embedding in zip(units, embeddings)
    ]
    vector_store.add_segments(items)
    return len(items)


async def ingest_manual_pair(
    source_text: str,
    target_text: str,
    source_lang: str,
    target_lang: str,
    document_title: str,
) -> str:
    embeddings = await ollama.embed([source_text.strip()])
    created_at = datetime.now(timezone.utc).isoformat()
    ids = vector_store.add_segments(
        [
            {
                "source_text": source_text.strip(),
                "target_text": target_text.strip(),
                "source_lang": source_lang,
                "target_lang": target_lang,
                "document_title": document_title or "Manual entry",
                "created_at": created_at,
                "embedding": embeddings[0],
            }
        ]
    )
    return ids[0]


def list_memory(source_lang: str | None, target_lang: str | None, limit: int, offset: int) -> list[dict]:
    return vector_store.list_recent(source_lang, target_lang, limit, offset)


def count_memory(source_lang: str | None, target_lang: str | None) -> int:
    return vector_store.count(source_lang, target_lang)


async def search_memory(
    query: str,
    source_lang: str | None,
    target_lang: str | None,
    limit: int,
) -> list[dict]:
    embeddings = await ollama.embed([query])
    results = vector_store.search_semantic(embeddings[0], limit * 3 if (source_lang or target_lang) else limit)
    if source_lang:
        results = [r for r in results if r.get("source_lang") == source_lang]
    if target_lang:
        results = [r for r in results if r.get("target_lang") == target_lang]
    return results[:limit]


def delete_memory(item_id: str) -> None:
    vector_store.delete(item_id)
