import re
from typing import Set

PRESERVED_ACRONYMS: Set[str] = {
    "AI", "ML", "RAG", "LLM", "API", "REST", "SQL", "CRUD", "JSON", "XML",
    "CSV", "HTML", "CSS", "HTTP", "HTTPS", "URL", "URI", "PDF", "RAM", "ROM",
    "CPU", "GPU", "OS", "UI", "UX", "ID", "BFS", "DFS", "OOP", "DB", "DBMS",
    "NLP", "CRAG", "RRF", "BERT", "GPT", "KNN", "SVM", "PCA", "GB", "MB",
    "KB", "TB", "FAQ", "CI", "CD", "DOCX", "PPTX", "XLSX", "SOTA", "HyDE",
    "BM25", "HNSW", "IR", "TF-IDF", "OLLAMA"
}

ROMAN_NUMERALS: Set[str] = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"}


def normalize_heading_phrase(phrase: str) -> str:
    """
    Converts an all-caps title or heading to readable Title Case,
    while preserving acronyms, Roman numerals, and minor words.
    Example: '1. EXECUTIVE SUMMARY & KEY TAKEAWAYS' -> '1. Executive Summary & Key Takeaways'
    """
    minor_words = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "by", "with", "in", "of"}
    words = phrase.split()
    res = []
    for idx, w in enumerate(words):
        if w in {"&", "+", "/", "-", "·", "•", ":"}:
            res.append(w)
            continue
        m = re.match(r"^([^a-zA-Z0-9]*)([a-zA-Z0-9_-]+)([^a-zA-Z0-9]*)$", w)
        if not m:
            res.append(w)
            continue
        lead, core, trail = m.groups()
        core_upper = core.upper()
        if core_upper in PRESERVED_ACRONYMS or core_upper in ROMAN_NUMERALS:
            res.append(f"{lead}{core_upper}{trail}")
        elif idx > 0 and core.lower() in minor_words:
            res.append(f"{lead}{core.lower()}{trail}")
        else:
            res.append(f"{lead}{core.capitalize()}{trail}")
    return " ".join(res)


def clean_and_enhance_text(text: str) -> str:
    """
    Cleans raw document text, PDF page extractions, and summary previews:
    - Eliminates spaced-out and glued header artifacts (e.g. 'A C H A P T E R' or 'ACHAPTER' -> 'Chapter')
    - Replaces corrupted characters (\ufffd -> ' - ') and middle dots
    - Disentangles joined sections (e.g. 'PARTAFoundations' -> 'Part A: Foundations')
    - Normalizes random all-caps headings and shouting words to pleasant, readable title/sentence case
    - Preserves standard technical acronyms (RAG, API, SQL, ML, etc.)
    """
    if not text:
        return ""

    # 1. Clean unicode replacement characters and non-printable control chars
    text = re.sub(r"[\xb7\u00b7\ufffd]", " - ", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 2. Fix glued or spaced-out Chapter and Part markers from PDF kerning
    text = re.sub(r"\bA\s*C\s*H\s*A\s*P\s*T\s*E\s*R\s*(\d*)", r"Chapter \1", text, flags=re.IGNORECASE)
    text = re.sub(r"\bACHAPTER\s*(\d*)", r"Chapter \1", text, flags=re.IGNORECASE)
    text = re.sub(r"\bC\s*H\s*A\s*P\s*T\s*E\s*R\s*(\d*)", r"Chapter \1", text, flags=re.IGNORECASE)
    text = re.sub(r"\bPART([A-Za-z0-9])([A-Z][a-z])", r"Part \1: \2", text)
    text = re.sub(r"\bP\s*A\s*R\s*T\s*([A-Za-z0-9])\b", r"Part \1", text, flags=re.IGNORECASE)
    text = re.sub(r"\bP\s+A\s+R\s+T\b", "Part", text, flags=re.IGNORECASE)

    # In this part / chapter
    text = re.sub(r"\bINTHISPART\s*([A-Z]?)", r"In this part: \1", text, flags=re.IGNORECASE)
    text = re.sub(r"\bI\s*N\s+T\s*H\s*I\s*S\s+P\s*A\s*R\s*T\b", "In this part:", text, flags=re.IGNORECASE)
    text = re.sub(r"\bINTHISCHAPTER\s*([A-Z]?)", r"In this chapter: \1", text, flags=re.IGNORECASE)
    text = re.sub(r"\bI\s*N\s+T\s*H\s*I\s*S\s+C\s*H\s*A\s*P\s*T\s*E\s*R\b", "In this chapter:", text, flags=re.IGNORECASE)

    # Split lowercase glued to capitalized word (e.g. 'modelA design' -> 'model A design')
    text = re.sub(r"([a-z])([A-Z]\s+[a-z])", r"\1 \2", text)

    # Generic spaced-out single letters (e.g., F O U N D A T I O N S -> Foundations)
    def _join_spaced_letters(m):
        raw = m.group(0)
        chars = [c for c in raw if c.isalpha()]
        word = "".join(chars)
        if word.upper() in PRESERVED_ACRONYMS:
            return word.upper()
        return word.capitalize()

    text = re.sub(r"\b(?:[A-Za-z]\s+){2,}[A-Za-z]\b", _join_spaced_letters, text)

    # 3. Clean runs of ALL-CAPS words (e.g. 'DATA MODELING FOUNDATIONS' -> 'Data Modeling Foundations')
    def _clean_caps_run(m):
        phrase = m.group(0)
        tokens = phrase.split()
        if all(re.sub(r"[^\w]", "", t).upper() in PRESERVED_ACRONYMS for t in tokens):
            return phrase
        return normalize_heading_phrase(phrase)

    text = re.sub(r"\b[A-Z]{2,}(?:\s+[A-Z]{2,})+\b", _clean_caps_run, text)

    # 4. Clean single long uppercase words (>3 letters) that aren't acronyms
    def _clean_single_word(m):
        w = m.group(0)
        if w.upper() in PRESERVED_ACRONYMS or w in ROMAN_NUMERALS:
            return w.upper()
        return w.capitalize()

    text = re.sub(r"\b[A-Z]{4,}\b", _clean_single_word, text)

    # 5. Spacing and punctuation normalization
    text = re.sub(r":+", ":", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    text = re.sub(r"\s*([·•])\s*", r" \1 ", text)
    text = text.strip()

    return text


def enhance_user_facing_answer(answer: str) -> str:
    """
    Enhances LLM generated responses, comparative syntheses, and summaries:
    - Protects markdown code blocks and inline code from being altered
    - Converts shouting markdown headings (### SUMMARY: -> ### Summary:)
    - Normalizes unnecessary ALL CAPS words and bold headers to readable Title/Sentence Case
    - Strictly protects source citations [Document, Page X]
    - Improves readability so the user does not get tired reading
    """
    if not answer or not answer.strip():
        return answer

    # Split into code blocks vs text blocks so code syntax is never modified
    parts = answer.split("```")
    cleaned_parts = []

    for i, part in enumerate(parts):
        # Odd indices are inside code blocks - leave untouched
        if i % 2 == 1:
            cleaned_parts.append(part)
            continue

        lines = part.split("\n")
        enhanced_lines = []

        for line in lines:
            line_str = line

            # Convert shouting markdown headings (e.g. ### KEY TAKEAWAYS: -> ### Key Takeaways:)
            heading_match = re.match(r"^(#{1,6}\s+)(.+)$", line_str)
            if heading_match:
                prefix = heading_match.group(1)
                full_title = heading_match.group(2)
                had_colon = full_title.endswith(":")
                title_clean = full_title.rstrip(":")
                colon_suffix = ":" if had_colon else ""
                line_str = f"{prefix}{normalize_heading_phrase(title_clean)}{colon_suffix}"

            # Convert bold shouting headers like **SUMMARY:** or **CORE CONCEPTS:**
            def _clean_bold_header(m):
                full_match = m.group(0)
                content = m.group(1)
                had_col = ":" in full_match
                core = content.rstrip(":")
                colon = ":" if had_col else ""
                return f"**{normalize_heading_phrase(core)}{colon}**"

            line_str = re.sub(r"\*\*([A-Z0-9\s&/\-\.,]{3,}):?\*\*", _clean_bold_header, line_str)

            # Mask and protect source citations [Doc Name, Page X]
            citations = []
            def _mask_citation(m):
                idx = len(citations)
                citations.append(m.group(0))
                return f"___CIT_MASK_{idx}___"

            line_masked = re.sub(r"\[[^\]]+\]", _mask_citation, line_str)

            # Mask inline code `...`
            inline_codes = []
            def _mask_inline_code(m):
                idx = len(inline_codes)
                inline_codes.append(m.group(0))
                return f"___INL_MASK_{idx}___"

            line_masked = re.sub(r"`[^`]+`", _mask_inline_code, line_masked)

            # Clean shouting uppercase words (>3 letters) outside code & citations
            def _clean_shouting_words(m):
                w = m.group(0)
                if w.upper() in PRESERVED_ACRONYMS or w in ROMAN_NUMERALS:
                    return w.upper()
                return w.capitalize()

            # Clean runs of ALL-CAPS words
            def _clean_line_caps_run(m):
                phrase = m.group(0)
                tokens = phrase.split()
                if all(re.sub(r"[^\w]", "", t).upper() in PRESERVED_ACRONYMS or t in ROMAN_NUMERALS for t in tokens):
                    return phrase
                # If it's a short phrase of shouting, convert to sentence case
                return " ".join(t.upper() if t.upper() in PRESERVED_ACRONYMS or t in ROMAN_NUMERALS else t.capitalize() for t in tokens)

            line_masked = re.sub(r"\b[A-Z]{2,}(?:\s+[A-Z]{2,})+\b", _clean_line_caps_run, line_masked)
            line_masked = re.sub(r"\b[A-Z]{4,}\b", _clean_shouting_words, line_masked)

            # Restore inline codes
            for idx, inl in enumerate(inline_codes):
                line_masked = line_masked.replace(f"___INL_MASK_{idx}___", inl)

            # Restore citations
            for idx, cit in enumerate(citations):
                line_masked = line_masked.replace(f"___CIT_MASK_{idx}___", cit)

            enhanced_lines.append(line_masked)

        cleaned_parts.append("\n".join(enhanced_lines))

    return "```".join(cleaned_parts)
