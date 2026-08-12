from datetime import datetime, timezone

from .alignment import align_tables
from .document_parser import Table
from .llm_alignment import align_documents_with_llm
from .ollama_client import OllamaClient
from .segmentation import split_sentences
from .vector_store import vector_store

ollama = OllamaClient()


async def preview_document_pair(
    source_text: str,
    source_tables: list[Table],
    target_text: str,
    target_tables: list[Table],
    source_lang: str,
    target_lang: str,
) -> dict:
    """Align a source document with its translation before anything is
    committed to the translation memory.

    Body text is segmented and aligned by the chat model in one step
    (app/llm_alignment.py) - real documents mix flowing prose, short
    list-like entries, and headings, and no rule-based paragraph-splitting
    heuristic told those apart consistently enough for a downstream
    similarity-based aligner to work with. Table cells are matched
    positionally instead (app/alignment.align_tables): a bare cell value
    (an element symbol, a lone number) has too little semantic content for
    the model or similarity search to place reliably, whereas a table's
    row/column structure reliably survives translation. The caller still
    reviews and can edit every pair before it is committed.
    """
    pairs = await align_documents_with_llm(source_text, target_text, source_lang, target_lang)
    pairs.extend(align_tables(source_tables, target_tables))
    gap_count = sum(1 for pair in pairs if not pair["source_text"].strip() or not pair["target_text"].strip())
    return {"pairs": pairs, "gap_count": gap_count}


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
