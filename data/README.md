# Data Directory Documentation

This directory contains the dataset documents used by the **RAG-Powered Document Assistant**.

## Directory Structure

```text
data/
├── raw/         # Raw source PDF files (academic lectures, CS textbooks, documentation)
├── processed/   # Intermediate processed JSON / chunk files (optional)
└── README.md    # Dataset guidelines and schema documentation
```

## Chosen Domain: University / Computer Science Educational Documents

The target domain focuses on core Computer Science and AI curriculum materials:
1. `cs_intro_python.pdf` - Computer Science & Python Fundamentals (Variables, Control Flow, Functions, OOP)
2. `cs_data_structures.pdf` - Data Structures & Algorithms (Arrays, Hash Tables, Trees, Sorting, Search Complexity)
3. `cs_machine_learning.pdf` - Machine Learning & AI Principles (Supervised vs Unsupervised, Neural Networks, RAG Architecture)

## Adding Custom Documents

To add new documents to the assistant:
1. Place `.pdf` files into `data/raw/`.
2. Ensure PDFs contain selectable text (not scanned images without OCR).
3. Re-run the ingestion pipeline script or notebook cell:
   ```bash
   python backend/app/services/ingestion.py
   ```
4. The persistent vector database in `backend/data/vector_store/` will be updated with new embeddings and page-level metadata.

## Document Metadata Schema

Each ingested chunk stores the following metadata attributes:
- `document`: Base filename of the PDF (e.g., `cs_intro_python.pdf`)
- `page`: 1-based page number where text was extracted
- `chunk_id`: Unique identifier string formatted as `{doc_name}_p{page_num}_c{chunk_index}`
