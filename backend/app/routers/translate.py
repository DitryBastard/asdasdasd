from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from ..docx_builder import build_translated_docx, translations_by_paragraph
from ..document_parser import extract_paragraphs, extract_paragraphs_docx
from ..schemas import TranslateRequest, TranslateResponse
from ..translation_service import translate_text

router = APIRouter(prefix="/api/translate", tags=["translate"])

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


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


@router.post("/document/formatted")
async def translate_document_formatted(
    file: UploadFile = File(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...),
):
    """Translate an uploaded .docx and return a new .docx with the same
    paragraph-level formatting as the original (see docx_builder.py for what
    that does and doesn't preserve). Re-translates from scratch rather than
    reusing a prior /document call's result, keeping the backend stateless.
    """
    filename = file.filename or "document.docx"
    if not filename.lower().endswith(".docx"):
        raise HTTPException(
            400, "Скачивание с оригинальным форматированием сейчас поддерживается только для .docx"
        )

    data = await file.read()
    try:
        paragraphs = extract_paragraphs_docx(data)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    text = "\n\n".join(paragraphs)
    if not text.strip():
        raise HTTPException(400, "Could not extract any text from the document")

    result = await translate_text(text, source_lang, target_lang)
    translations = translations_by_paragraph(paragraphs, result["segments"])
    docx_bytes = build_translated_docx(data, translations)

    download_name = f"{filename[:-5]}_translated.docx" if filename.lower().endswith(".docx") else f"{filename}_translated.docx"
    return Response(
        content=docx_bytes,
        media_type=DOCX_MEDIA_TYPE,
        headers={"Content-Disposition": _content_disposition(download_name)},
    )


def _content_disposition(filename: str) -> str:
    ascii_fallback = filename.encode("ascii", errors="ignore").decode("ascii") or "translated.docx"
    return f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{quote(filename)}'
