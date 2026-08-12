import io
import re

from docx import Document
from pypdf import PdfReader

_BLANK_LINE_SPLIT = re.compile(r"\n\s*\n+")


def extract_paragraphs_docx(data: bytes) -> list[str]:
    document = Document(io.BytesIO(data))
    return [p.text.strip() for p in document.paragraphs if p.text.strip()]


def extract_paragraphs_pdf(data: bytes) -> list[str]:
    reader = PdfReader(io.BytesIO(data))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
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
    raise ValueError(f"Unsupported file type: {filename}. Use .docx, .pdf, or .txt")
