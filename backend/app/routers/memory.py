from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from .. import memory_service
from ..document_parser import extract_paragraphs
from ..schemas import (
    CommitDocumentPairsRequest,
    DocumentPairPreviewResponse,
    ManualMemoryEntry,
    MemoryListResponse,
)

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("", response_model=MemoryListResponse)
async def list_memory(
    source_lang: str | None = None,
    target_lang: str | None = None,
    query: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    if query:
        items = await memory_service.search_memory(query, source_lang, target_lang, limit)
        total = len(items)
    else:
        items = memory_service.list_memory(source_lang, target_lang, limit, offset)
        total = memory_service.count_memory(source_lang, target_lang)
    return {"items": items, "total": total}


@router.post("/entry")
async def add_manual_entry(entry: ManualMemoryEntry):
    if not entry.source_text.strip() or not entry.target_text.strip():
        raise HTTPException(400, "Both source and target text are required")
    item_id = await memory_service.ingest_manual_pair(
        entry.source_text, entry.target_text, entry.source_lang, entry.target_lang, entry.document_title
    )
    return {"id": item_id}


@router.post("/documents/preview", response_model=DocumentPairPreviewResponse)
async def preview_document_pair(
    source_file: UploadFile = File(...),
    target_file: UploadFile = File(...),
):
    source_data = await source_file.read()
    target_data = await target_file.read()
    try:
        source_paragraphs = extract_paragraphs(source_file.filename or "source.txt", source_data)
        target_paragraphs = extract_paragraphs(target_file.filename or "target.txt", target_data)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not source_paragraphs or not target_paragraphs:
        raise HTTPException(400, "Could not extract text from one of the documents")
    return memory_service.preview_document_pair(source_paragraphs, target_paragraphs)


@router.post("/documents/commit")
async def commit_document_pairs(req: CommitDocumentPairsRequest):
    if not req.pairs:
        raise HTTPException(400, "No pairs to add")
    count = await memory_service.ingest_pairs(
        [pair.model_dump() for pair in req.pairs],
        req.source_lang,
        req.target_lang,
        req.document_title,
    )
    return {"added_segments": count}


@router.delete("/{item_id}")
async def delete_entry(item_id: str):
    memory_service.delete_memory(item_id)
    return {"status": "deleted"}
