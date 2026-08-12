from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..document_parser import extract_paragraphs
from ..schemas import TranslateRequest, TranslateResponse
from ..translation_service import translate_text

router = APIRouter(prefix="/api/translate", tags=["translate"])


@router.post("", response_model=TranslateResponse)
async def translate(req: TranslateRequest):
    if not req.text.strip():
        raise HTTPException(400, "Text is empty")
    return await translate_text(req.text, req.source_lang, req.target_lang)


@router.post("/document", response_model=TranslateResponse)
async def translate_document(
    file: UploadFile = File(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...),
):
    data = await file.read()
    try:
        paragraphs = extract_paragraphs(file.filename or "upload.txt", data)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    text = "\n\n".join(paragraphs)
    if not text.strip():
        raise HTTPException(400, "Could not extract any text from the document")
    return await translate_text(text, source_lang, target_lang)
