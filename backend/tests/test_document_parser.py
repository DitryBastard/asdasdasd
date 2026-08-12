import pytest

from app.document_parser import extract_paragraphs, extract_paragraphs_docx, extract_paragraphs_pdf


def test_malformed_pdf_raises_value_error_not_pypdf_internals():
    # A real-world malformed/truncated PDF (missing a proper trailer) used to
    # bubble up as an unhandled pypdf.errors.PdfStreamError -> HTTP 500.
    garbage = b"%PDF-1.4\nnot a real pdf body"
    with pytest.raises(ValueError, match="PDF"):
        extract_paragraphs_pdf(garbage)


def test_malformed_docx_raises_value_error():
    garbage = b"this is not a zip/docx file at all"
    with pytest.raises(ValueError, match="docx"):
        extract_paragraphs_docx(garbage)


def test_extract_paragraphs_rejects_unsupported_extension():
    with pytest.raises(ValueError, match="Неподдерживаемый"):
        extract_paragraphs("notes.rtf", b"whatever")
