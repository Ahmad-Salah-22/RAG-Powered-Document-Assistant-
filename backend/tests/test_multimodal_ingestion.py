import io
import zipfile
import pytest
from app.services.ingestion import extract_from_bytes, _extract_csv, _extract_docx


def test_extract_csv():
    csv_data = b"name,role,department\nAlice,AI Engineer,R&D\nBob,Data Scientist,Analytics"
    text = _extract_csv(csv_data)
    assert "Alice" in text
    assert "AI Engineer" in text
    assert "Bob" in text


def test_extract_from_bytes_csv():
    csv_data = b"id,topic,score\n101,Retrieval-Augmented Generation,98\n102,Vector Databases,95"
    pages, stats = extract_from_bytes(csv_data, "evaluation_data.csv")
    assert stats["file_type"] == "csv"
    assert stats["char_count"] > 0
    assert len(pages) == 1
    assert "Retrieval-Augmented Generation" in pages[0]["text"]


def test_extract_docx_synthetic():
    # Construct a minimal in-memory docx zip
    bio = io.BytesIO()
    doc_xml = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        b'<w:body>'
        b'<w:p><w:r><w:t>Deep Learning Architectures and Embeddings</w:t></w:r></w:p>'
        b'<w:p><w:r><w:t>Transformers revolutionized natural language processing.</w:t></w:r></w:p>'
        b'</w:body>'
        b'</w:document>'
    )
    with zipfile.ZipFile(bio, "w") as zf:
        zf.writestr("word/document.xml", doc_xml)
    
    docx_bytes = bio.getvalue()
    pages, stats = extract_from_bytes(docx_bytes, "research_notes.docx")
    assert stats["file_type"] == "docx"
    assert "Deep Learning Architectures" in pages[0]["text"]
    assert "Transformers revolutionized" in pages[0]["text"]
