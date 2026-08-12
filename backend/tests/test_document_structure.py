import io

import pytest
from docx import Document
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.document_parser import extract_structure, extract_structure_docx, extract_structure_pdf


def _build_sample_docx() -> bytes:
    document = Document()
    document.add_paragraph("Intro paragraph about the material.")
    table = document.add_table(rows=2, cols=3)
    values = [["Fe", "Ti", "Mo"], ["178.29", "0.5", "I"]]
    for row_idx, row_values in enumerate(values):
        for col_idx, value in enumerate(row_values):
            table.cell(row_idx, col_idx).text = value
    document.add_paragraph("Closing paragraph after the table.")

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _build_sample_pdf() -> bytes:
    # Intro and closing text live on separate pages purely so this fixture
    # produces two distinguishable page_texts entries to exercise the
    # page-join behavior; extract_structure_pdf no longer tries to guess
    # paragraph boundaries within that text (see app/llm_alignment.py for
    # why - the model does that job now).
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    table = Table([["Fe", "Ti", "Mo"], ["178.29", "0.5", "I"]])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    elements = [
        Paragraph("Intro paragraph about the material.", styles["Normal"]),
        PageBreak(),
        table,
        Spacer(1, 12),
        Paragraph("Closing paragraph after the table.", styles["Normal"]),
    ]
    doc.build(elements)
    return buffer.getvalue()


def test_extract_structure_docx_keeps_table_separate_from_text():
    text, tables = extract_structure_docx(_build_sample_docx())

    assert text == "Intro paragraph about the material.\n\nClosing paragraph after the table."
    assert tables == [[["Fe", "Ti", "Mo"], ["178.29", "0.5", "I"]]]


def test_extract_structure_docx_rejects_malformed_file():
    with pytest.raises(ValueError, match="docx"):
        extract_structure_docx(b"not a docx file")


def test_extract_structure_pdf_detects_table_and_prose_separately():
    text, tables = extract_structure_pdf(_build_sample_pdf())

    assert "Intro paragraph" in text
    assert "Closing paragraph" in text
    # The table's own cell values must not also leak into the prose stream -
    # otherwise cells get aligned/stored twice, once as loose text and once
    # as structured table data.
    assert "Fe" not in text and "Ti" not in text
    assert len(tables) == 1
    assert tables[0][0] == ["Fe", "Ti", "Mo"]
    assert tables[0][1] == ["178.29", "0.5", "I"]


def test_extract_structure_dispatches_by_extension():
    docx_text, docx_tables = extract_structure("original.docx", _build_sample_docx())
    pdf_text, pdf_tables = extract_structure("original.pdf", _build_sample_pdf())

    assert docx_tables and pdf_tables
    assert "Intro paragraph about the material." in docx_text
    assert "Intro paragraph about the material." in pdf_text


def test_extract_structure_txt_has_no_tables():
    text, tables = extract_structure("notes.txt", "First.\n\nSecond.".encode("utf-8"))
    assert text == "First.\n\nSecond."
    assert tables == []


def test_extract_structure_rejects_unsupported_extension():
    with pytest.raises(ValueError, match="Неподдерживаемый"):
        extract_structure("notes.rtf", b"whatever")
