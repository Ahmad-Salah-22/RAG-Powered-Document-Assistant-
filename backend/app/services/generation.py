import httpx
import re
from typing import Tuple, List, Optional, Dict, Any
from app.utils.logging_config import logger
from app.core.config import settings

from app.utils.text_enhancer import enhance_user_facing_answer

PROMPT_TEMPLATES = {
    "academic": """You are an approachable, strictly document-grounded Academic Research Assistant.

Your task is to answer the user's question using ONLY the provided document context blocks below.

Strict Grounding & Readability Rules:
1. Base your answer ENTIRELY on the provided context blocks.
2. When the question asks for criteria, principles, components, summaries, or checklists, extract and synthesize all corresponding items found in the context, and present them clearly with their explanations and definitions.
3. If the context does not contain relevant information to answer, state clearly: "I could not find relevant information in the provided documents to answer your question."
4. Do NOT invent facts or make outside assumptions.
5. Always cite your sources precisely using the format: [Document Name, Page X].
6. Style & Readability: Write in natural, friendly, and easy-to-read prose. Avoid writing words, headings, or phrases in ALL CAPS unless they are standard acronyms (e.g., RAG, API, SQL). Break complex concepts into clean, digestible points so the reader does not get tired.

{chat_history_block}
Document Context:
{context}

User Question:
{question}

Grounded Academic Answer with Citations:""",

    "concise": """You are an executive RAG assistant providing ultra-concise, high-impact, and easy-to-read answers.

Strict Grounding & Readability Rules:
1. Base your answer ONLY on the provided context.
2. When criteria, checklists, or core principles are requested, list all matching items directly with their core definitions and citations.
3. Provide the direct answer in clean bullet points or concise sentences.
4. Cite sources at the end of each bullet: [Document Name, Page X].
5. If the context does not answer the question, state: "I could not find relevant information in the provided documents to answer your question."
6. Style: Friendly, natural sentence casing. Do NOT write in ALL CAPS.

{chat_history_block}
Document Context:
{context}

User Question:
{question}

Concise Grounded Answer:""",

    "detailed": """You are an expert, patient tutor providing clear, comprehensive explanations based on document context.

Strict Grounding & Readability Rules:
1. Base your answer ONLY on the provided context.
2. When criteria, methodologies, or principles are requested, explain each element thoroughly with its definition, rationale, key questions, and examples from the context.
3. Break down the concept step-by-step with clean, intuitive section headings in title case.
4. Include relevant definitions, formulas, or structured details if present in the text.
5. Always cite specific sources: [Document Name, Page X].
6. If the context is insufficient, state clearly: "I could not find relevant information in the provided documents to answer your question."
7. Style & Readability: Write in a pleasant, conversational tone. Avoid robotic language and avoid writing words or headings in ALL CAPS. Keep explanations effortless to read.

{chat_history_block}
Document Context:
{context}

User Question:
{question}

Detailed Tutorial-Style Answer with Citations:""",

    "summary": """You are an executive document synthesis specialist creating an easy-to-digest summary.

Strict Grounding & Readability Rules:
1. Base your synthesis ONLY on the provided context.
2. When summarizing or evaluating, present the core ideas, main findings, and actionable takeaways.
3. Provide:
   - **Executive Summary** (1-2 clear, readable paragraphs in natural sentence case)
   - **Key Takeaways & Core Points** (3-6 clean bullet points with citations: [Document Name, Page X])
4. If not found in documents, state: "I could not find relevant information in the provided documents to answer your question."
5. Style: Highly legible and user-friendly. Never use unnecessary ALL CAPS words.

{chat_history_block}
Document Context:
{context}

User Question:
{question}

Executive Summary & Key Takeaways:"""
}


async def check_ollama_availability(ollama_host: str = settings.OLLAMA_HOST) -> bool:
    """
    Checks if local Ollama daemon is active and responsive.
    """
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{ollama_host.rstrip('/')}/api/tags")
            return resp.status_code == 200
    except Exception as e:
        logger.debug(f"Ollama health check ping failed: {e}")
        return False


async def get_available_ollama_models(ollama_host: str = settings.OLLAMA_HOST) -> List[str]:
    """
    Queries Ollama to fetch installed models.
    """
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{ollama_host.rstrip('/')}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                return models
    except Exception:
        pass
    return ["llama3:8b", "mistral", "phi3", "gemma2"]


def format_chat_history(chat_history: Optional[List[Dict[str, str]]]) -> str:
    """Formats recent turns into a prompt block."""
    if not chat_history:
        return ""
    lines = ["CONVERSATION HISTORY:"]
    for turn in chat_history[-6:]:  # Keep last 3 exchanges
        role = turn.get("role", "user").capitalize()
        content = turn.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    lines.append("")
    return "\n".join(lines)


def is_off_topic_or_ungrounded_answer(answer: str) -> bool:
    """
    Detects if the generated answer indicates that the requested information
    is missing from, ungrounded in, or off-topic relative to the provided documents.
    """
    if not answer or not answer.strip():
        return True

    ans_lower = answer.lower()

    # Direct refusal / missing information patterns
    patterns = [
        r"could not find",
        r"cannot find",
        r"can not find",
        r"unable to find",
        r"not found in the (?:provided )?documents?",
        r"not mentioned in the (?:provided )?documents?",
        r"do(?:es)? not contain (?:any )?information",
        r"do(?:es)? not discuss",
        r"do(?:es)? not cover",
        r"no information (?:about|regarding) .* in the (?:provided )?documents?",
        r"outside the scope of the (?:provided )?documents?",
        r"unable to provide an answer based on the (?:provided )?(?:context|documents?)",
        r"unable to answer based on the (?:provided )?(?:context|documents?)",
        r"information is not (?:present|available) in the (?:provided )?documents?",
        r"not (?:present|available) in the (?:provided )?(?:context|documents?)",
        r"(?:context|documents?) do(?:es)? not (?:contain|mention|provide|discuss|cover)",
        r"i am unable to find",
        r"i cannot answer this based on the provided",
        r"cannot be answered (?:using|from) the provided",
    ]

    for pat in patterns:
        if re.search(pat, ans_lower):
            return True

    return False


def generate_extractive_fallback_answer(question: str, context: str) -> str:
    """
    Intelligent heuristic fallback used when local Ollama is offline or not installed.
    Extracts the most relevant grounded paragraphs from context blocks and cites them accurately.
    """
    if not context or not context.strip():
        return "I could not find relevant information in the provided documents to answer your question."

    blocks = context.split("\n---\n")
    keywords = set(re.findall(r"\w+", question.lower())) - {"what", "is", "the", "of", "and", "in", "a", "to", "how", "are", "for"}

    scored_blocks = []
    for b in blocks:
        b_lower = b.lower()
        score = sum(1 for kw in keywords if kw in b_lower)
        scored_blocks.append((score, b))

    # If no keywords matched any context blocks, this query is completely off-topic
    if not scored_blocks or max(score for score, _ in scored_blocks) == 0:
        return "I could not find relevant information in the provided documents to answer your question."

    scored_blocks.sort(key=lambda x: x[0], reverse=True)
    best_blocks = [b[1] for b in scored_blocks[:3] if b[1].strip() and b[0] > 0]

    if not best_blocks:
        return "I could not find relevant information in the provided documents to answer your question."

    extracted_lines = []
    for b in best_blocks:
        extracted_lines.append(b.strip())

    combined_text = "\n\n".join(extracted_lines)

    return (
        f"**[Offline Direct Retrieval Engine]**\n\n"
        f"Based on the indexed document passages directly matching your query:\n\n"
        f"{combined_text}\n\n"
        f"---\n"
        f"*💡 Note: Local Ollama daemon is currently offline. The answer above was constructed directly from verified vector store context. "
        f"Start `ollama serve` to enable full neural generation with `{settings.OLLAMA_MODEL}`.*"
    )


async def generate_grounded_answer(
    question: str,
    context: str,
    ollama_host: str = settings.OLLAMA_HOST,
    ollama_model: str = settings.OLLAMA_MODEL,
    timeout: float = settings.OLLAMA_TIMEOUT,
    system_prompt_mode: str = "academic",
    chat_history: Optional[List[Dict[str, str]]] = None,
    allow_fallback: bool = True
) -> Tuple[str, bool, bool]:
    """
    Invokes Ollama local LLM to generate grounded answer from context.
    Falls back gracefully to extractive grounded synthesis if Ollama is unreachable.

    Returns:
        Tuple[str, bool, bool]: (Answer text, Success flag, Fallback used flag)
    """
    if not context or not context.strip():
        logger.info("Empty context provided to generation service. Returning ungrounded fallback.")
        return (
            "I could not find relevant information in the provided documents to answer your question.",
            True,
            False
        )

    # Choose prompt template
    template = PROMPT_TEMPLATES.get(system_prompt_mode.lower(), PROMPT_TEMPLATES["academic"])
    chat_history_block = format_chat_history(chat_history)
    prompt = template.format(
        context=context,
        question=question,
        chat_history_block=chat_history_block
    )

    logger.info(f"Sending prompt to Ollama LLM model '{ollama_model}' at '{ollama_host}' (mode: {system_prompt_mode})")

    payload = {
        "model": ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{ollama_host.rstrip('/')}/api/generate",
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                answer_text = data.get("response", "").strip()
                logger.info("Successfully generated grounded response from Ollama.")
                return enhance_user_facing_answer(answer_text), True, False
            elif response.status_code == 404:
                error_msg = f"Ollama model '{ollama_model}' not found. Please run 'ollama pull {ollama_model}'."
                logger.warning(error_msg)
                if allow_fallback:
                    return enhance_user_facing_answer(generate_extractive_fallback_answer(question, context)), True, True
                return f"Error: {error_msg}", False, False
            else:
                error_msg = f"Ollama HTTP {response.status_code}: {response.text}"
                logger.warning(error_msg)
                if allow_fallback:
                    return enhance_user_facing_answer(generate_extractive_fallback_answer(question, context)), True, True
                return f"Error connecting to LLM service: {error_msg}", False, False

    except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
        logger.warning(f"Ollama connection unavailable or timed out ({conn_err}). Engaging intelligent fallback.")
        if allow_fallback:
            return enhance_user_facing_answer(generate_extractive_fallback_answer(question, context)), True, True
        return f"Service Unavailable: Ollama is offline at {ollama_host}.", False, False
    except Exception as e:
        logger.error(f"Unexpected error during generation: {str(e)}", exc_info=True)
        if allow_fallback:
            return enhance_user_facing_answer(generate_extractive_fallback_answer(question, context)), True, True
        return f"Error: {str(e)}", False, False


_page_summary_cache: Dict[Tuple[str, int, int], Dict[str, Any]] = {}


def generate_extractive_page_summary(page_text: str, document_name: str, page_number: int) -> Dict[str, Any]:
    """
    Produces structured extractive summary from raw page text without requiring an external LLM.
    """
    clean_text = " ".join(page_text.split())
    if not clean_text or len(clean_text) < 20:
        return {
            "main_topic": "Visual or Blank Page",
            "summary": "This page does not contain extractable text content. It may contain charts, figures, or unindexed scanned images.",
            "key_points": [
                "No readable machine text extracted.",
                "Inspect the visual PDF viewer on the right to review diagrams or images."
            ],
            "model_used": "Extractive Fallback"
        }

    # Split text into sentences
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_text) if len(s.strip()) > 20]
    
    # Try to derive main topic from early lines or first sentence
    first_lines = [l.strip() for l in page_text.split("\n") if l.strip()]
    main_topic = None
    if first_lines and len(first_lines[0]) < 80 and not first_lines[0].endswith("."):
        main_topic = first_lines[0]
    elif sentences:
        main_topic = sentences[0][:60] + "..." if len(sentences[0]) > 60 else sentences[0]
    else:
        main_topic = f"Content Overview (Page {page_number})"

    # Clean main topic
    main_topic = re.sub(r"^[0-9.\-–\s]+", "", main_topic).strip() or f"Page {page_number} Overview"

    # Select top 2-3 most informative sentences for summary
    summary_sentences = sentences[:3] if len(sentences) >= 3 else sentences
    summary = " ".join(summary_sentences) if summary_sentences else clean_text[:300]

    # Generate key points from subsequent sentences or bullet items
    key_points = []
    # Check for existing bullet points in page text
    bullet_matches = re.findall(r"(?:^|\n)\s*[•\-\*]\s*([^\n]+)", page_text)
    if bullet_matches:
        for b in bullet_matches[:5]:
            b_clean = b.strip()
            if len(b_clean) > 15:
                key_points.append(b_clean)

    if not key_points and len(sentences) > 2:
        for s in sentences[2:6]:
            if s not in summary:
                key_points.append(s)

    if not key_points:
        # Fallback chunks
        words = clean_text.split()
        if len(words) > 30:
            key_points = [
                f"Covers key concepts: {', '.join(words[:10])}...",
                f"Section highlights: {', '.join(words[20:30])}..."
            ]
        else:
            key_points = ["Contains brief introductory or concluding statements for this section."]

    return {
        "main_topic": enhance_user_facing_answer(main_topic),
        "summary": enhance_user_facing_answer(summary),
        "key_points": [enhance_user_facing_answer(kp) for kp in key_points[:5]],
        "model_used": "Extractive Fallback"
    }


async def summarize_page_content(
    document_name: str,
    page_number: int,
    page_text: str,
    ollama_host: str = settings.OLLAMA_HOST,
    ollama_model: str = settings.OLLAMA_MODEL,
    timeout: float = 30.0,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Generates a structured, concise AI summary and key takeaways for a specific page of a document.
    Returns:
        Dict with keys: main_topic, summary, key_points, model_used, latency_ms
    """
    import time
    t_start = time.perf_counter()

    char_len = len(page_text.strip()) if page_text else 0
    cache_key = (document_name, page_number, char_len)

    if not force_refresh and cache_key in _page_summary_cache:
        cached = dict(_page_summary_cache[cache_key])
        cached["latency_ms"] = 0.5
        return cached

    if not page_text or char_len < 25:
        fallback_res = generate_extractive_page_summary(page_text, document_name, page_number)
        fallback_res["latency_ms"] = round((time.perf_counter() - t_start) * 1000.0, 2)
        _page_summary_cache[cache_key] = fallback_res
        return fallback_res

    # Attempt generation with Ollama
    ollama_active = await check_ollama_availability(ollama_host)
    if ollama_active:
        prompt = f"""You are an expert document analyst. Summarize Page {page_number} of "{document_name}" based on the text below.

Instructions:
1. Provide a single phrase for the Main Topic.
2. Provide a 2-3 sentence clear Executive Summary of what this page discusses.
3. Provide 3-5 concise bullet points highlighting the most important takeaways, definitions, findings, or criteria.
4. Use clear, friendly, natural sentence casing. Avoid all-caps shouting.

Strict Output Format:
TOPIC: <Single phrase representing this page>
SUMMARY: <2-3 sentence summary>
KEY POINTS:
- <Key takeaway 1>
- <Key takeaway 2>
- <Key takeaway 3>

Page Content:
{page_text[:3500]}

Structured Summary:"""

        payload = {
            "model": ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(f"{ollama_host.rstrip('/')}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    response_text = data.get("response", "").strip()

                    # Parse structured response
                    topic_match = re.search(r"TOPIC:\s*(.+?)(?=\n|SUMMARY:|$)", response_text, re.IGNORECASE)
                    summary_match = re.search(r"SUMMARY:\s*(.+?)(?=\nKEY POINTS:|\n-|$)", response_text, re.IGNORECASE | re.DOTALL)
                    key_points_match = re.search(r"KEY POINTS:\s*(.+)$", response_text, re.IGNORECASE | re.DOTALL)

                    main_topic = topic_match.group(1).strip() if topic_match else f"Page {page_number} Overview"
                    summary = summary_match.group(1).strip() if summary_match else ""
                    
                    key_points = []
                    if key_points_match:
                        raw_pts = key_points_match.group(1).strip()
                        for line in raw_pts.split("\n"):
                            pt = re.sub(r"^[•\-\*\d.]+\s*", "", line).strip()
                            if pt and len(pt) > 5:
                                key_points.append(pt)

                    if not summary and response_text:
                        summary = response_text[:350]

                    if not key_points and summary:
                        # Extract sentences as points
                        sents = [s.strip() for s in summary.split(".") if len(s.strip()) > 15]
                        key_points = sents[:3]

                    result = {
                        "main_topic": enhance_user_facing_answer(main_topic),
                        "summary": enhance_user_facing_answer(summary),
                        "key_points": [enhance_user_facing_answer(k) for k in key_points[:5]],
                        "model_used": ollama_model,
                        "latency_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
                    }
                    _page_summary_cache[cache_key] = result
                    return result

        except Exception as e:
            logger.warning(f"Ollama page summarization failed ({e}). Reverting to extractive summary.")

    # Extractive fallback
    fallback_res = generate_extractive_page_summary(page_text, document_name, page_number)
    fallback_res["latency_ms"] = round((time.perf_counter() - t_start) * 1000.0, 2)
    _page_summary_cache[cache_key] = fallback_res
    return fallback_res
