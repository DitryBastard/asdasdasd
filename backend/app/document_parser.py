import io
import re

from docx import Document
from pypdf import PdfReader

_BLANK_LINE_SPLIT = re.compile(r"\n\s*\n+")


def iter_docx_paragraphs(document) -> list:
    """Every paragraph in a docx: body text, then table cells.

    Not strict reading order when tables are interleaved with body text, but
    every paragraph is visited exactly once - which is all extraction
    (translate) and reconstruction (formatted download, see docx_builder.py)
    need, as long as both use this same shared traversal so their paragraph
    sets line up. Nested tables (a table inside a cell) are not walked.
    """
    paragraphs = list(document.paragraphs)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                paragraphs.extend(cell.paragraphs)
    return paragraphs


def extract_paragraphs_docx(data: bytes) -> list[str]:
    try:
        document = Document(io.BytesIO(data))
        return [p.text.strip() for p in iter_docx_paragraphs(document) if p.text.strip()]
    except Exception as exc:
        # python-docx can fail in many file-specific ways on a malformed or
        # non-Word file (bad zip, missing parts, ...) - surface one clear,
        # actionable message instead of a raw 500.
        raise ValueError(
            "Не удалось прочитать .docx — файл повреждён или это не настоящий Word-документ."
        ) from exc


def extract_paragraphs_pdf(data: bytes) -> list[str]:
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        # Real-world PDFs (scans, exports from various document systems)
        # frequently have non-standard trailers/streams that make pypdf give
        # up entirely. There is no reliable in-process fix for that, so fail
        # with a clear, actionable message instead of a raw 500.
        raise ValueError(
            "Не удалось прочитать PDF — файл повреждён или использует нестандартный формат. "
            "Попробуйте пересохранить его (например, через печать в PDF в браузере или "
            "'Сохранить как' в Adobe/Word) или загрузите .docx, если он есть."
        ) from exc
    paragraphs = [p.strip() for p in _BLANK_LINE_SPLIT.split(text) if p.strip()]
    if len(paragraphs) <= 1:
        # Some PDFs don't have blank-line paragraph breaks in their extracted
        # text; fall back to one paragraph per non-empty line.
        paragraphs = [line.strip() for line in text.split("\n") if line.strip()]
    return paragraphs


def extract_paragraphs_txt(data: bytes) -> list[str]:
    text = data.decode("utf-8", errors="replace")
    return [p.strip() for p in _BLANK_LINE_SPLIT.split(text) if p.strip()]


def extract_paragraphs(filename: str, data: bytes) -> list[str]:
    lower = filename.lower()
    if lower.endswith(".docx"):
        return extract_paragraphs_docx(data)
    if lower.endswith(".pdf"):
        return extract_paragraphs_pdf(data)
    if lower.endswith(".txt"):
        return extract_paragraphs_txt(data)
    raise ValueError(f"Неподдерживаемый тип файла: {filename}. Используйте .docx, .pdf или .txt")
