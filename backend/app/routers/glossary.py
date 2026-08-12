from fastapi import APIRouter, HTTPException

from .. import glossary_store
from ..schemas import GlossaryEntryIn, GlossaryListResponse

router = APIRouter(prefix="/api/glossary", tags=["glossary"])


@router.get("", response_model=GlossaryListResponse)
async def list_glossary(source_lang: str | None = None, target_lang: str | None = None):
    return {"items": glossary_store.list_entries(source_lang, target_lang)}


@router.post("")
async def add_glossary_entry(entry: GlossaryEntryIn):
    if not entry.source_term.strip() or not entry.target_term.strip():
        raise HTTPException(400, "Both source and target terms are required")
    added = glossary_store.add_entry(
        entry.source_term, entry.target_term, entry.source_lang, entry.target_lang, entry.note
    )
    return added


@router.delete("/{entry_id}")
async def delete_glossary_entry(entry_id: str):
    glossary_store.delete_entry(entry_id)
    return {"status": "deleted"}
