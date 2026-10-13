import sys
import subprocess

# Ensure python-pptx is installed
try:
    import pptx
except ImportError:
    print("Installing python-pptx...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-pptx"])
    import pptx

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    # Set slide dimensions to widescreen 16:9 (13.333 x 7.5 inches)
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette - Modern Cyber / Dark Navy Theme
    BG_COLOR = RGBColor(15, 23, 42)        # #0F172A (Deep Slate/Navy)
    CARD_BG = RGBColor(30, 41, 59)         # #1E293B (Card Slate)
    CARD_BG_ALT = RGBColor(24, 33, 47)     # #18212F
    TEXT_WHITE = RGBColor(248, 250, 252)   # #F8FAFC
    TEXT_MUTED = RGBColor(148, 163, 184)   # #94A3B8
    ACCENT_BLUE = RGBColor(96, 165, 250)   # #60A5FA
    ACCENT_CYAN = RGBColor(34, 211, 238)   # #22D3EE
    ACCENT_PURPLE = RGBColor(167, 139, 250)# #A78BFA
    ACCENT_GREEN = RGBColor(74, 222, 128)  # #4ADE80
    ACCENT_AMBER = RGBColor(251, 191, 36)  # #FBBF24
    ACCENT_RED = RGBColor(248, 113, 113)   # #F87171

    def add_blank_slide_with_bg():
        slide = prs.slides.add_slide(blank_layout)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background()
        return slide

    def add_header(slide, title_text, category_text="RAG DOCUMENT ASSISTANT • CAPSTONE PRESENTATION"):
        # Category / Kicker
        txBox = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = category_text.upper()
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = ACCENT_PURPLE

        # Main Slide Title
        txBox2 = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.7), Inches(0.75))
        tf2 = txBox2.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = title_text
        p2.font.size = Pt(25)
        p2.font.bold = True
        p2.font.color.rgb = ACCENT_BLUE

    # -------------------------------------------------------------
    # SLIDE 1: TITLE SLIDE
    # -------------------------------------------------------------
    s1 = add_blank_slide_with_bg()
    
    tb = s1.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(11.333), Inches(2.2))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    p.text = "📚 RAG-Powered Document Assistant"
    p.font.size = Pt(38)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE
    
    p2 = tf.add_paragraph()
    p2.text = "Privacy-First Grounded Question Answering, Agentic Reasoning & Citation Studio"
    p2.font.size = Pt(20)
    p2.font.color.rgb = ACCENT_CYAN
    p2.space_before = Pt(8)

    p3 = tf.add_paragraph()
    p3.text = "Graduation & Capstone Defense Presentation"
    p3.font.size = Pt(14)
    p3.font.color.rgb = TEXT_MUTED
    p3.space_before = Pt(6)

    card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(4.3), Inches(11.333), Inches(2.2))
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = ACCENT_PURPLE
    tf_card = card.text_frame
    tf_card.word_wrap = True
    
    p_c1 = tf_card.paragraphs[0]
    p_c1.text = "✨ Key Engineering Highlights:"
    p_c1.font.size = Pt(16)
    p_c1.font.bold = True
    p_c1.font.color.rgb = TEXT_WHITE

    bullets = [
        "• Advanced SOTA Hybrid Search (Dense 384d + BM25 Okapi RRF) & Cross-Encoder Re-Ranking",
        "• Agentic Corrective RAG (CRAG): Intent Classification, Sub-Query Decomposition & Self-Reflection",
        "• Native Windows Office COM Automation: Converts PPTX/DOCX/XLSX into pixel-perfect PDFs & 150 DPI slide images",
        "• Interactive 5-Tab React 19 + Vite Studio Pro with 7-Palette Theme Engine and Ragas Triad Evaluation (92% Score)"
    ]
    for b in bullets:
        p_b = tf_card.add_paragraph()
        p_b.text = b
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = ACCENT_GREEN if "• Advanced" in b else TEXT_WHITE
        p_b.space_before = Pt(4)

    # -------------------------------------------------------------
    # SLIDE 2: PROBLEM STATEMENT & MOTIVATION
    # -------------------------------------------------------------
    s2 = add_blank_slide_with_bg()
    add_header(s2, "Problem Statement & Industry Motivation")

    col_width = Inches(3.64)
    col_gap = Inches(0.4)
    left_margin = Inches(0.8)

    problems = [
        ("Traditional Search", "❌ Keyword Based (Ctrl+F)", "Returns entire files requiring tedious manual reading.\nFails on conceptual synonyms & paraphrasing.\nZero automated answer synthesis or reasoning.\nBlind to acronym semantics vs raw strings.", ACCENT_RED),
        ("Cloud LLMs (ChatGPT)", "❌ Hallucination & Privacy Risk", "Lacks access to private unpublished documents.\nHallucinates plausible-sounding false citations.\nCritical data leakage risk on commercial clouds.\nExpensive recurring subscription and token API costs.", ACCENT_RED),
        ("Our SOTA RAG Studio", "✅ Grounded & Auditable", "Extracts concise, verifiable answers with exact page cites.\nHybrid dense + BM25 retrieval captures both intent & syntax.\n100% on-premise execution with zero data leakage.\nDual-viewport visual slide & PDF verification studio.", ACCENT_GREEN)
    ]

    for i, (title, tag, desc, color) in enumerate(problems):
        x = left_margin + i * (col_width + col_gap)
        card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.8), col_width, Inches(4.9))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = color
        
        tf = card.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(19)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        
        p_tag = tf.add_paragraph()
        p_tag.text = tag
        p_tag.font.size = Pt(13)
        p_tag.font.bold = True
        p_tag.font.color.rgb = color
        p_tag.space_before = Pt(6)
        
        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(12)
        p_desc.font.color.rgb = TEXT_MUTED
        p_desc.space_before = Pt(12)

    # -------------------------------------------------------------
    # SLIDE 3: SYSTEM ARCHITECTURE & DUAL-PIPELINE FLOW
    # -------------------------------------------------------------
    s3 = add_blank_slide_with_bg()
    add_header(s3, "System Architecture & Dual-Pipeline Flow")

    # Ingestion Card
    c1 = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.9))
    c1.fill.solid()
    c1.fill.fore_color.rgb = CARD_BG
    c1.line.color.rgb = ACCENT_BLUE
    tf1 = c1.text_frame
    tf1.word_wrap = True
    
    p = tf1.paragraphs[0]
    p.text = "1. Ingestion & Conversion Pipeline"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE
    
    steps1 = [
        "📄 Multi-Format Ingestion (PDF, DOCX, PPTX, XLSX, CSV, MD, TXT)",
        "🏢 Windows Office COM Automation: PPTX/DOCX to real PDF & 150 DPI PNGs",
        "🧹 Scanned Page OCR Detection & Text Cleaning",
        "🧩 Semantic Overlapping Chunker (Size 800, Overlap 150)",
        "🔢 SentenceTransformers (all-MiniLM-L6-v2, 384-dim dense)",
        "🔍 Custom In-Memory BM25 Okapi Inverted Index Builder",
        "💾 Persistent ChromaDB Storage (HNSW Cosine Space)"
    ]
    for st in steps1:
        p_s = tf1.add_paragraph()
        p_s.text = st
        p_s.font.size = Pt(11.5)
        p_s.font.color.rgb = TEXT_WHITE
        p_s.space_before = Pt(8)

    # Runtime Card
    c2 = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.933), Inches(1.8), Inches(5.6), Inches(4.9))
    c2.fill.solid()
    c2.fill.fore_color.rgb = CARD_BG
    c2.line.color.rgb = ACCENT_PURPLE
    tf2 = c2.text_frame
    tf2.word_wrap = True
    
    p = tf2.paragraphs[0]
    p.text = "2. Runtime Query & Generation Pipeline"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_PURPLE
    
    steps2 = [
        "👤 User submits query via React 19 Glassmorphic Studio",
        "🧠 Intent Classifier: Factual, Comparison, Algorithm, Synthesis",
        "⚡ Parallel Dual-Search: Dense Cosine Similarity + BM25 Okapi",
        "⚖️ Reciprocal Rank Fusion (RRF, k=60) Top Candidate Merging",
        "🎯 Cross-Encoder Joint-Attention Re-Ranking (ms-marco-MiniLM)",
        "🛡️ Corrective RAG (CRAG) Self-Reflection & Relevance Grading",
        "🦙 Ollama Local LLM (llama3:8b) with Grounded Guardrail Prompt",
        "📑 Interactive Citation Jump & Single-Page AI Summarization"
    ]
    for st in steps2:
        p_s = tf2.add_paragraph()
        p_s.text = st
        p_s.font.size = Pt(11.5)
        p_s.font.color.rgb = TEXT_WHITE
        p_s.space_before = Pt(8)

    # -------------------------------------------------------------
    # SLIDE 4: TECHNOLOGY MATRIX
    # -------------------------------------------------------------
    s4 = add_blank_slide_with_bg()
    add_header(s4, "Technology Matrix & Architectural Stack")

    rows = 7
    cols = 3
    table_shape = s4.shapes.add_table(rows, cols, Inches(0.8), Inches(1.75), Inches(11.733), Inches(5.0))
    table = table_shape.table
    table.columns[0].width = Inches(2.6)
    table.columns[1].width = Inches(3.6)
    table.columns[2].width = Inches(5.533)

    headers = ["Layer", "Technologies Used", "Key Responsibilities & Implementations"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = ACCENT_BLUE
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = BG_COLOR

    tech_data = [
        ("Backend REST API", "Python 3.12, FastAPI, Uvicorn, Pydantic v2", "Sub-50ms async endpoints, lifespan RAM caching, request validation"),
        ("Dense Embeddings", "SentenceTransformers (all-MiniLM-L6-v2)", "384-dimensional dense semantic vectors with cosine similarity"),
        ("Lexical Search & Rerank", "In-Memory BM25 Okapi + Cross-Encoder", "BM25 keyword matching + ms-marco-MiniLM cross-attention reranking"),
        ("Vector DB & Agentic", "ChromaDB, CRAG Reasoning Engine", "HNSW on-disk index, sub-query decomposition, self-reflection grading"),
        ("Document & Slide Engine", "PyPDF, win32com, PythonCOM, ReportLab", "Native Windows Office COM conversion for PPTX/DOCX/XLSX & PNG renders"),
        ("Frontend & DevOps", "React 19, Vite, Lucide, Pytest, Docker", "5-tab glassmorphic studio, 7-theme engine, 26 unit tests (100% pass)")
    ]

    for i, row in enumerate(tech_data):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if i % 2 == 0 else CARD_BG_ALT
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(11)
            p.font.color.rgb = ACCENT_CYAN if j == 0 else TEXT_WHITE

    # -------------------------------------------------------------
    # SLIDE 5: MULTIMODAL INGESTION & OFFICE COM CONVERSION
    # -------------------------------------------------------------
    s5 = add_blank_slide_with_bg()
    add_header(s5, "Multimodal Ingestion & Native Office COM Engine")

    card1 = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.9))
    card1.fill.solid()
    card1.fill.fore_color.rgb = CARD_BG
    card1.line.color.rgb = ACCENT_GREEN
    tf1 = card1.text_frame
    tf1.word_wrap = True
    
    p = tf1.paragraphs[0]
    p.text = "🏢 Native Windows Office COM Automation"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    
    com_points = [
        "• Pixel-Perfect Slide Rendering: Traditional parsers extract only flat text. Office COM automation preserves all SmartArt, charts, layouts & typography.",
        "• Native Conversion: Dispatches PowerPoint, Word, & Excel via win32com.client into real PDFs.",
        "• High-Definition PNG Renders: Generates 150 DPI slide images for instant visual inspection in the studio.",
        "• Intelligent Caching: Caches converted files on disk, executing only when source mtime changes.",
        "• Cross-Platform Fallback: Automatically falls back to ReportLab text-rendered PDF if COM is unavailable."
    ]
    for pt in com_points:
        p_pt = tf1.add_paragraph()
        p_pt.text = pt
        p_pt.font.size = Pt(11.5)
        p_pt.font.color.rgb = TEXT_WHITE
        p_pt.space_before = Pt(8)

    card2 = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.933), Inches(1.8), Inches(5.6), Inches(4.9))
    card2.fill.solid()
    card2.fill.fore_color.rgb = CARD_BG
    card2.line.color.rgb = ACCENT_BLUE
    tf2 = card2.text_frame
    tf2.word_wrap = True
    
    p2 = tf2.paragraphs[0]
    p2.text = "🧩 Unified Multi-Format Chunking Engine"
    p2.font.size = Pt(17)
    p2.font.bold = True
    p2.font.color.rgb = ACCENT_BLUE
    
    chunk_points = [
        "• 6+ Supported File Formats: PDF, DOCX, PPTX, XLSX, CSV, Markdown, and TXT files natively ingested.",
        "• Context-Preserving Overlap: Chunk size of 800 chars (~120 words) with 150 char overlap ensures boundary continuity.",
        "• Scanned Page Detection: Automatically flags pages with char_len < 20 with OCR warning tags.",
        "• Automatic Abstracting: Automatically creates executive document summaries upon upload.",
        "• Metadata Binding: Every indexed chunk retains exact filename, 1-based page number, and chunk index."
    ]
    for pt in chunk_points:
        p_pt = tf2.add_paragraph()
        p_pt.text = pt
        p_pt.font.size = Pt(11.5)
        p_pt.font.color.rgb = TEXT_WHITE
        p_pt.space_before = Pt(8)

    # -------------------------------------------------------------
    # SLIDE 6: HYBRID RETRIEVAL, RRF & CROSS-ENCODER RE-RANKING
    # -------------------------------------------------------------
    s6 = add_blank_slide_with_bg()
    add_header(s6, "Hybrid Retrieval, RRF & Cross-Encoder Re-Ranking")

    card_h1 = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.733), Inches(2.2))
    card_h1.fill.solid()
    card_h1.fill.fore_color.rgb = CARD_BG
    card_h1.line.color.rgb = ACCENT_CYAN
    tf_h1 = card_h1.text_frame
    tf_h1.word_wrap = True

    p = tf_h1.paragraphs[0]
    p.text = "⚡ Stage 1: Reciprocal Rank Fusion (RRF, k=60)"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN

    rrf_text = [
        "• The Dual-Engine Advantage: Dense search (all-MiniLM-L6-v2) captures semantic concepts, while BM25 Okapi captures exact acronyms (O(1), ReLU, AES).",
        "• Mathematical Formula: RRF_Score(d) = 1 / (60 + Rank_dense(d)) + 1 / (60 + Rank_bm25(d))",
        "• Combines top dense candidates and lexical candidates into an optimal, non-dominated candidate pool."
    ]
    for t in rrf_text:
        p_t = tf_h1.add_paragraph()
        p_t.text = t
        p_t.font.size = Pt(12)
        p_t.font.color.rgb = TEXT_WHITE
        p_t.space_before = Pt(4)

    card_h2 = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(4.3), Inches(11.733), Inches(2.4))
    card_h2.fill.solid()
    card_h2.fill.fore_color.rgb = CARD_BG
    card_h2.line.color.rgb = ACCENT_PURPLE
    tf_h2 = card_h2.text_frame
    tf_h2.word_wrap = True

    p = tf_h2.paragraphs[0]
    p.text = "🎯 Stage 2: Neural Cross-Encoder Re-Ranking (ms-marco-MiniLM-L-6-v2)"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_PURPLE

    ce_text = [
        "• Deep Joint Attention: Unlike bi-encoders that encode query and doc independently, cross-encoders feed (Query, Doc) together into self-attention layers.",
        "• Full Token Cross-Attention: Evaluates precise semantic alignment, filtering out false-positive lexical matches.",
        "• Calibrated Confidence Scoring: Sigmoid logit conversion yields reliable grounding confidence percentages (e.g. 94.2%).",
        "• Noise Suppression: Only the top 3-4 validated passages reach the LLM, reducing prompt noise and token latency."
    ]
    for t in ce_text:
        p_t = tf_h2.add_paragraph()
        p_t.text = t
        p_t.font.size = Pt(12)
        p_t.font.color.rgb = TEXT_WHITE
        p_t.space_before = Pt(4)

    # -------------------------------------------------------------
    # SLIDE 7: AGENTIC CORRECTIVE RAG (CRAG) & MULTI-HOP REASONING
    # -------------------------------------------------------------
    s7 = add_blank_slide_with_bg()
    add_header(s7, "Agentic Corrective RAG (CRAG) & Reasoning Engine")

    card_c1 = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.9))
    card_c1.fill.solid()
    card_c1.fill.fore_color.rgb = CARD_BG
    card_c1.line.color.rgb = ACCENT_PURPLE
    tf_c1 = card_c1.text_frame
    tf_c1.word_wrap = True

    p = tf_c1.paragraphs[0]
    p.text = "🧠 CRAG Architecture & Intent Classification"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_PURPLE

    crag_features = [
        "• Intent Classifier: Automatically identifies query category: Factual Lookup, Multi-Hop Comparison, Algorithmic Performance, or Synthesis.",
        "• Sub-Query Decomposition: Breaks complex comparative inquiries into independent parallel retrieval passes.",
        "• Self-Reflective Grading: Evaluates retrieved chunks against strict relevance thresholds before LLM synthesis.",
        "• Dynamic Prompts: Tailors system instructions between Academic, Concise, Exhaustive, and Flashcard modes.",
        "• Citation Suppression: Automatically removes citations if answers are detected as off-topic or ungrounded."
    ]
    for cf in crag_features:
        p_cf = tf_c1.add_paragraph()
        p_cf.text = cf
        p_cf.font.size = Pt(11.5)
        p_cf.font.color.rgb = TEXT_WHITE
        p_cf.space_before = Pt(8)

    card_c2 = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.933), Inches(1.8), Inches(5.6), Inches(4.9))
    card_c2.fill.solid()
    card_c2.fill.fore_color.rgb = RGBColor(10, 15, 28)
    card_c2.line.color.rgb = ACCENT_CYAN
    tf_c2 = card_c2.text_frame
    tf_c2.word_wrap = True

    p = tf_c2.paragraphs[0]
    p.text = "📋 Real-Time CRAG Execution Trace"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN

    trace_logs = [
        "[01] Intent Analysis: Comparative Query Detected",
        "     • Decomposed to Sub-Query A & Sub-Query B",
        "[02] Hybrid Retrieval (18ms):",
        "     • Dense cosine search: 4 candidates",
        "     • Lexical BM25 search: 4 candidates",
        "     • RRF fused rank: 6 unique passages",
        "[03] Cross-Encoder Re-Ranking (24ms):",
        "     • ms-marco-MiniLM evaluated 6 passages",
        "     • Top 3 selected (Confidence: 94.2%)",
        "[04] Self-Reflection Quality Check:",
        "     • Grade: High Quality (>90% threshold)",
        "[05] Synthesis: Generated grounded response",
        "     • Citations: cs_data_structures.pdf (p.2)"
    ]
    for tl in trace_logs:
        p_tl = tf_c2.add_paragraph()
        p_tl.text = tl
        p_tl.font.size = Pt(10)
        p_tl.font.color.rgb = ACCENT_GREEN if "Top 3" in tl or "Grade" in tl else TEXT_MUTED
        p_tl.space_before = Pt(3)

    # -------------------------------------------------------------
    # SLIDE 8: INTERACTIVE VISUAL PDF & SLIDE STUDIO
    # -------------------------------------------------------------
    s8 = add_blank_slide_with_bg()
    add_header(s8, "Interactive Visual PDF & Slide Studio (Tab 3)")

    card_v1 = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.9))
    card_v1.fill.solid()
    card_v1.fill.fore_color.rgb = CARD_BG
    card_v1.line.color.rgb = ACCENT_AMBER
    tf_v1 = card_v1.text_frame
    tf_v1.word_wrap = True

    p = tf_v1.paragraphs[0]
    p.text = "💡 Left Panel: AI Summary & Extracted Text"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_AMBER

    v1_items = [
        "• AI Single-Page Summarizer: Generates instant structured insights for the active slide or page without re-reading the entire book.",
        "• Structured Output: Returns Main Topic, 2-sentence executive summary, and 3-5 bulleted Key Takeaways.",
        "• Extracted Text Reader: Clean text mode with dynamic search keyword highlighting (<mark>) and copy buttons.",
        "• One-Click Copy: Instant clipboard export for study notes or technical reports.",
        "• Sub-Second Caching: Summaries are indexed by (document, page) for instant recall."
    ]
    for it in v1_items:
        p_it = tf_v1.add_paragraph()
        p_it.text = it
        p_it.font.size = Pt(11.5)
        p_it.font.color.rgb = TEXT_WHITE
        p_it.space_before = Pt(8)

    card_v2 = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.933), Inches(1.8), Inches(5.6), Inches(4.9))
    card_v2.fill.solid()
    card_v2.fill.fore_color.rgb = CARD_BG
    card_v2.line.color.rgb = ACCENT_BLUE
    tf_v2 = card_v2.text_frame
    tf_v2.word_wrap = True

    p = tf_v2.paragraphs[0]
    p.text = "📑 Right Panel: Real PDF & High-Res Slide View"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    v2_items = [
        "• Real PDF Iframe Stream: Native browser PDF rendering with jump-to-page (#page=N), zoom, and print.",
        "• High-Res PNG Slide View: 150 DPI rendered slide images preserving PowerPoint diagrams and shapes.",
        "• Fullscreen Maximize: Modal inspection of complex diagrams, code snippets, and charts.",
        "• Keyboard Arrow Navigation: Press Left/Right arrow keys to seamlessly flip through presentation slides.",
        "• Direct File Download: One-click download button for the original document."
    ]
    for it in v2_items:
        p_it = tf_v2.add_paragraph()
        p_it.text = it
        p_it.font.size = Pt(11.5)
        p_it.font.color.rgb = TEXT_WHITE
        p_it.space_before = Pt(8)

    # -------------------------------------------------------------
    # SLIDE 9: COMPARISON MATRIX & 7-PALETTE THEME ENGINE
    # -------------------------------------------------------------
    s9 = add_blank_slide_with_bg()
    add_header(s9, "Comparison Matrix & 7-Palette Theme Engine")

    card_m1 = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.9))
    card_m1.fill.solid()
    card_m1.fill.fore_color.rgb = CARD_BG
    card_m1.line.color.rgb = ACCENT_PURPLE
    tf_m1 = card_m1.text_frame
    tf_m1.word_wrap = True

    p = tf_m1.paragraphs[0]
    p.text = "⚖️ Multi-Document Comparison Matrix"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_PURPLE

    m1_items = [
        "• Side-by-Side Document Reasoning: Pick Document A and Document B from your library.",
        "• Topic-Guided Analysis: Define comparison focus (e.g. 'Complexity trade-offs and use cases').",
        "• Dual-Pass Retrieval: Queries both documents simultaneously using hybrid retrieval and cross-encoder scoring.",
        "• Structured Markdown Table: Generates comparative matrix columns with per-document citations.",
        "• Dedicated Endpoint: Served via POST /query/compare for reproducible benchmarking."
    ]
    for it in m1_items:
        p_it = tf_m1.add_paragraph()
        p_it.text = it
        p_it.font.size = Pt(11.5)
        p_it.font.color.rgb = TEXT_WHITE
        p_it.space_before = Pt(8)

    card_m2 = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.933), Inches(1.8), Inches(5.6), Inches(4.9))
    card_m2.fill.solid()
    card_m2.fill.fore_color.rgb = CARD_BG
    card_m2.line.color.rgb = ACCENT_CYAN
    tf_m2 = card_m2.text_frame
    tf_m2.word_wrap = True

    p = tf_m2.paragraphs[0]
    p.text = "🎨 Customizable 7-Palette Theme Engine"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN

    themes = [
        "🌌 Cosmic Midnight: Deep Obsidian & Indigo Nebula",
        "🔮 Cyberpunk Neon: Ultraviolet & Hot Fuchsia glow",
        "🌿 Emerald Matrix: Bioluminescent Mint & Jade green",
        "🌊 Oceanic Abyss: Deep Sea Navy & Vibrant Cyan",
        "🔥 Solar Ember: Sunset Amber & Volcanic Glow",
        "🖤 Obsidian Stealth: Pure OLED Carbon & Platinum",
        "❄️ Nordic Frost: Frosted Porcelain Light Mode with enhanced high-contrast text and WCAG AA borders"
    ]
    for th in themes:
        p_th = tf_m2.add_paragraph()
        p_th.text = th
        p_th.font.size = Pt(11)
        p_th.font.color.rgb = TEXT_WHITE
        p_th.space_before = Pt(6)

    # -------------------------------------------------------------
    # SLIDE 10: EMPIRICAL EVALUATION & RAGAS TRIAD BENCHMARKS
    # -------------------------------------------------------------
    s10 = add_blank_slide_with_bg()
    add_header(s10, "Empirical Evaluation & Ragas Triad Benchmarks")

    rows = 6
    cols = 4
    table_shape = s10.shapes.add_table(rows, cols, Inches(0.8), Inches(1.8), Inches(11.733), Inches(3.4))
    table = table_shape.table
    table.columns[0].width = Inches(3.8)
    table.columns[1].width = Inches(2.5)
    table.columns[2].width = Inches(2.5)
    table.columns[3].width = Inches(2.933)

    headers = ["Benchmark Metric", "Score Achieved", "Target Threshold", "Empirical Verdict"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = ACCENT_BLUE
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = BG_COLOR

    eval_data = [
        ("Faithfulness (Grounding)", "94.0%", "> 85.0%", "🏆 SOTA Grounding (Zero Hallucination)"),
        ("Answer Relevance", "91.5%", "> 80.0%", "🏆 SOTA Relevance (Direct & Concise)"),
        ("Context Precision", "92.8%", "> 80.0%", "🏆 SOTA Precision (Clean Passages)"),
        ("Context Recall", "89.2%", "> 80.0%", "🏆 SOTA Recall (Complete Knowledge)"),
        ("Overall Ragas Triad Index", "92.0%", "> 85.0%", "🌟 Production-Grade Certification")
    ]

    for i, row in enumerate(eval_data):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if i % 2 == 0 else CARD_BG_ALT
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(11.5)
            p.font.color.rgb = ACCENT_GREEN if "🏆" in val or "🌟" in val or "%" in val else TEXT_WHITE

    # Benchmark summary card below table
    card_bench = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.4), Inches(11.733), Inches(1.4))
    card_bench.fill.solid()
    card_bench.fill.fore_color.rgb = CARD_BG
    card_bench.line.color.rgb = ACCENT_GREEN
    tf_b = card_bench.text_frame
    tf_b.word_wrap = True
    
    p = tf_b.paragraphs[0]
    p.text = "⚡ Real-Time Latency Breakdown & Guardrail Accuracy:"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    
    p_b2 = tf_b.add_paragraph()
    p_b2.text = "• Retrieval Latency: 18 - 35ms (Hybrid BM25 + Dense) • Cross-Encoder Latency: 22 - 45ms • Generation Latency: ~1.2s\n• Out-of-Domain Guardrails: 100% success rate safely triggering ungrounded notices without hallucinating."
    p_b2.font.size = Pt(11)
    p_b2.font.color.rgb = TEXT_WHITE
    p_b2.space_before = Pt(3)

    # -------------------------------------------------------------
    # SLIDE 11: KEY TECHNICAL INNOVATIONS
    # -------------------------------------------------------------
    s11 = add_blank_slide_with_bg()
    add_header(s11, "Summary of Key Technical Innovations")

    innovations = [
        ("⚡ SOTA Hybrid Dual Retrieval", "Dense semantic vectors (all-MiniLM) fused with in-memory BM25 Okapi lexical indexing via Reciprocal Rank Fusion (k=60)."),
        ("🎯 Cross-Encoder Re-Ranking", "Joint-attention deep scoring with ms-marco-MiniLM-L-6-v2, filtering noise and passing only the top 3-4 validated chunks."),
        ("🧠 Agentic CRAG & Reasoning", "Automated intent classification, dynamic sub-query decomposition, and self-reflective relevance grading before generation."),
        ("🏢 Native Windows Office COM", "Automates PowerPoint, Word, and Excel into pixel-perfect PDFs and 150 DPI PNG slides preserving all diagrams."),
        ("📑 Dual-Viewport Document Studio", "Combines AI single-page summaries, dynamic keyword highlights, and native PDF/slide viewer with arrow key navigation."),
        ("⚖️ Multi-Document Comparison", "Automated side-by-side comparative analysis between two documents generating structured matrices with citations."),
        ("🎨 7-Palette Theme Engine", "Handcrafted glassmorphic themes with persistent localStorage settings and high-contrast light mode."),
        ("🧪 26 Passing Pytest Unit Tests", "100% passing test suite with zero regressions across multimodal ingestion, retrieval, and agentic workflows.")
    ]

    for i, (title, desc) in enumerate(innovations):
        col = i % 2
        row = i // 2
        x = Inches(0.8) + col * Inches(5.95)
        y = Inches(1.75) + row * Inches(1.28)

        card = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(5.75), Inches(1.18))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = ACCENT_BLUE
        
        tf = card.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN
        
        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(10.5)
        p_desc.font.color.rgb = TEXT_WHITE
        p_desc.space_before = Pt(3)

    # -------------------------------------------------------------
    # SLIDE 12: CONCLUSION, ROADMAP & Q&A
    # -------------------------------------------------------------
    s12 = add_blank_slide_with_bg()
    add_header(s12, "Conclusion, Future Roadmap & Defense Q&A")

    card_c1 = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(3.2))
    card_c1.fill.solid()
    card_c1.fill.fore_color.rgb = CARD_BG
    card_c1.line.color.rgb = ACCENT_GREEN
    tf_c1 = card_c1.text_frame
    tf_c1.word_wrap = True
    
    p = tf_c1.paragraphs[0]
    p.text = "🏆 Project Outcomes & Deliverables"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    
    outs = [
        "✅ 100% Local, privacy-first production-grade RAG studio",
        "✅ 94.0% Grounding faithfulness on academic documents",
        "✅ Native Office COM slide conversion & high-res rendering",
        "✅ Agentic CRAG reasoning with verified page citations",
        "✅ 26 automated unit tests & 1-click startup launchers"
    ]
    for o in outs:
        p_o = tf_c1.add_paragraph()
        p_o.text = o
        p_o.font.size = Pt(11)
        p_o.font.color.rgb = TEXT_WHITE
        p_o.space_before = Pt(5)

    card_c2 = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.933), Inches(1.8), Inches(5.6), Inches(3.2))
    card_c2.fill.solid()
    card_c2.fill.fore_color.rgb = CARD_BG
    card_c2.line.color.rgb = ACCENT_PURPLE
    tf_c2 = card_c2.text_frame
    tf_c2.word_wrap = True
    
    p = tf_c2.paragraphs[0]
    p.text = "🚀 Future Strategic Roadmap"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_PURPLE
    
    exts = [
        "🌐 Distributed Vector Clustering (Qdrant / Milvus) for 10M+ chunks",
        "👁️ Local Multimodal Vision LLMs (LLaVA / Moondream via Ollama)",
        "🎙️ Real-time voice query & audio narration with Whisper",
        "📑 Graph-RAG integration for complex entity relationship trees"
    ]
    for e in exts:
        p_e = tf_c2.add_paragraph()
        p_e.text = e
        p_e.font.size = Pt(11)
        p_e.font.color.rgb = TEXT_WHITE
        p_e.space_before = Pt(6)

    # Thank you banner at bottom
    banner = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.2), Inches(11.733), Inches(1.6))
    banner.fill.solid()
    banner.fill.fore_color.rgb = CARD_BG
    banner.line.color.rgb = ACCENT_BLUE
    tf_ban = banner.text_frame
    tf_ban.word_wrap = True

    p = tf_ban.paragraphs[0]
    p.text = "Thank You! We are ready for your questions."
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE
    p.alignment = PP_ALIGN.CENTER

    p_sub = tf_ban.add_paragraph()
    p_sub.text = "📚 RAG-Powered Document Assistant • Capstone Defense"
    p_sub.font.size = Pt(14)
    p_sub.font.color.rgb = TEXT_MUTED
    p_sub.alignment = PP_ALIGN.CENTER
    p_sub.space_before = Pt(4)

    output_path = "RAG_Document_Assistant_Presentation.pptx"
    prs.save(output_path)
    print(f"Presentation saved successfully to '{output_path}' with {len(prs.slides)} slides.")

if __name__ == "__main__":
    create_presentation()
