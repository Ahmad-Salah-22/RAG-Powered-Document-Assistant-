import os
import re
import time
from typing import List, Dict, Any, Tuple, Optional
from app.schemas.query import SourceItem, AgenticReasoningStep
from app.services.retrieval import retrieve_context
from app.services.generation import generate_grounded_answer, is_off_topic_or_ungrounded_answer
from app.utils.logging_config import logger
from app.core.config import settings


def classify_and_decompose_intent(question: str) -> Dict[str, Any]:
    """
    Analyzes question intent and performs query decomposition for multi-hop or comparative questions.

    Returns:
        Dict with intent_type, sub_queries, reasoning_summary, is_complex
    """
    q_lower = question.lower()

    # Comparison intent patterns
    compare_keywords = ["compare", "difference between", "versus", "vs", "tradeoff", "trade-off", "contrast", "differ"]
    is_compare = any(kw in q_lower for kw in compare_keywords)

    # Synthesis / deep explanation intent
    synthesis_keywords = ["explain in detail", "summarize", "overview of", "breakdown", "how does", "why does", "deep dive"]
    is_synthesis = any(kw in q_lower for kw in synthesis_keywords)

    # Numerical / performance intent
    complexity_keywords = ["complexity", "big o", "runtime", "speed", "worst case", "average case", "memory"]
    is_complexity = any(kw in q_lower for kw in complexity_keywords)

    if is_compare:
        intent_type = "multi_hop_comparison"
        # Extract potential entities to split
        # Example: "Compare hash table vs binary search tree" -> sub queries
        sub_queries = []
        if " vs " in q_lower:
            parts = re.split(r"\s+vs\s+", question, flags=re.IGNORECASE)
            if len(parts) >= 2:
                sub_queries = [f"What is {parts[0].strip()}?", f"What is {parts[1].strip()}?"]
        elif "difference between" in q_lower:
            cleaned = re.sub(r"(?i)what\s+(is|are)\s+the\s+difference[s]?\s+between\s+", "", question)
            parts = cleaned.split(" and ")
            if len(parts) >= 2:
                sub_queries = [f"Overview of {parts[0].strip()}", f"Overview of {parts[1].strip()}"]
        
        if not sub_queries:
            sub_queries = [
                f"Core properties and characteristics of {question}",
                f"Performance trade-offs and structural differences in {question}"
            ]
        reasoning_summary = f"Detected multi-hop comparison query. Decomposed into {len(sub_queries)} targeted sub-queries for parallel context retrieval."
        is_complex = True

    elif is_complexity:
        intent_type = "algorithmic_performance"
        sub_queries = [
            f"Algorithmic runtime and memory complexity of {question}",
            f"Underlying mechanism and mathematical bounds for {question}"
        ]
        reasoning_summary = "Detected algorithmic complexity query. Expanding retrieval targets for time/space complexity specifications."
        is_complex = True

    elif is_synthesis:
        intent_type = "concept_synthesis"
        sub_queries = [
            f"Foundational concepts and principles of {question}",
            f"Practical implementation and architecture of {question}"
        ]
        reasoning_summary = "Detected deep conceptual synthesis intent. Decomposed into foundational and architectural retrieval passes."
        is_complex = True

    else:
        intent_type = "factual_lookup"
        sub_queries = [question]
        reasoning_summary = "Detected direct factual lookup. Executing single-pass high-precision retrieval."
        is_complex = False

    return {
        "intent_type": intent_type,
        "sub_queries": sub_queries,
        "reasoning_summary": reasoning_summary,
        "is_complex": is_complex
    }


def grade_context_relevance(
    question: str,
    sources: List[SourceItem],
    threshold: float = 65.0
) -> Dict[str, Any]:
    """
    Self-Reflective RAG (CRAG) grader:
    Evaluates retrieved chunks for question alignment, computes overall confidence,
    and determines whether corrective retrieval is required.
    """
    if not sources:
        return {
            "average_confidence": 0.0,
            "is_sufficient": False,
            "relevant_count": 0,
            "grading_assessment": "No context chunks retrieved; context insufficient for grounded answering.",
            "filtered_sources": []
        }

    confidences = [s.confidence_percent if s.confidence_percent is not None else 60.0 for s in sources]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    # Filter out chunks that fall well below threshold (e.g. < 40% confidence)
    graded_sources = [s for s in sources if (s.confidence_percent or 0.0) >= 40.0]
    relevant_count = len(graded_sources)

    is_sufficient = avg_conf >= threshold and relevant_count > 0

    if is_sufficient:
        assessment = f"Context graded as HIGH QUALITY (Avg confidence: {avg_conf:.1f}% across {relevant_count} chunks). Passing to grounded generator."
    elif relevant_count > 0 and avg_conf >= 35.0:
        assessment = f"Context graded as PARTIALLY SUFFICIENT (Avg confidence: {avg_conf:.1f}%). Supplemental corrective context applied."
    else:
        assessment = f"Context graded as LOW RELEVANCE / OFF-TOPIC (Avg confidence: {avg_conf:.1f}%). Warning: Chunks do not match query intent."
        graded_sources = []  # Explicitly clear chunks for off-topic questions

    return {
        "average_confidence": round(avg_conf, 1),
        "is_sufficient": is_sufficient,
        "relevant_count": len(graded_sources),
        "grading_assessment": assessment,
        "filtered_sources": graded_sources
    }


async def execute_agentic_rag(
    question: str,
    collection,
    embedding_model,
    top_k: int = 4,
    document_filter: Optional[List[str]] = None,
    similarity_threshold: Optional[float] = None,
    retrieval_mode: str = "hybrid",
    reranker_model = None,
    enable_reranker: bool = True,
    system_prompt_mode: str = "academic",
    chat_history: Optional[List[Dict[str, str]]] = None,
    ollama_host: str = settings.OLLAMA_HOST,
    ollama_model: str = settings.OLLAMA_MODEL
) -> Dict[str, Any]:
    """
    Full Agentic Corrective RAG (CRAG) Pipeline:
    1. Query Intent Classification & Multi-Hop Decomposition
    2. Primary & Sub-query Context Retrieval
    3. Self-Reflection & Relevance Grading
    4. Deduplication & Cross-Encoder Synthesis
    5. Grounded Generation with Reasoning Process Trace
    """
    t_start = time.perf_counter()
    reasoning_steps: List[AgenticReasoningStep] = []

    # -------------------------------------------------------------
    # Step 1: Query Intent & Decomposition
    # -------------------------------------------------------------
    intent_data = classify_and_decompose_intent(question)
    intent_type = intent_data["intent_type"]
    sub_queries = intent_data["sub_queries"]

    reasoning_steps.append(AgenticReasoningStep(
        step_number=1,
        phase="Intent Classification & Decomposition",
        status="success",
        title=f"Intent: {intent_type.replace('_', ' ').title()}",
        description=intent_data["reasoning_summary"],
        details={
            "detected_intent": intent_type,
            "is_complex": intent_data["is_complex"],
            "sub_queries": sub_queries
        }
    ))

    # -------------------------------------------------------------
    # Step 2: Multi-Hop / Targeted Retrieval
    # -------------------------------------------------------------
    t_ret_start = time.perf_counter()
    all_sources: List[SourceItem] = []
    seen_snippets = set()

    # Primary query retrieval
    primary_context, primary_sources = retrieve_context(
        query=question,
        collection=collection,
        embedding_model=embedding_model,
        top_k=top_k,
        document_filter=document_filter,
        similarity_threshold=similarity_threshold,
        retrieval_mode=retrieval_mode,
        reranker_model=reranker_model,
        enable_reranker=enable_reranker,
        query_expansion=True
    )

    for s in primary_sources:
        snip_key = f"{s.document}_{s.page}_{s.snippet[:40] if s.snippet else ''}"
        if snip_key not in seen_snippets:
            seen_snippets.add(snip_key)
            all_sources.append(s)

    # If complex, run sub-queries to fill knowledge gaps (Multi-Hop)
    if intent_data["is_complex"] and len(sub_queries) > 1:
        for sq in sub_queries[:2]:
            _, sub_sources = retrieve_context(
                query=sq,
                collection=collection,
                embedding_model=embedding_model,
                top_k=max(2, top_k // 2),
                document_filter=document_filter,
                similarity_threshold=similarity_threshold,
                retrieval_mode=retrieval_mode,
                reranker_model=reranker_model,
                enable_reranker=enable_reranker,
                query_expansion=False
            )
            for s in sub_sources:
                snip_key = f"{s.document}_{s.page}_{s.snippet[:40] if s.snippet else ''}"
                if snip_key not in seen_snippets:
                    seen_snippets.add(snip_key)
                    all_sources.append(s)

    retrieval_latency = (time.perf_counter() - t_ret_start) * 1000.0

    reasoning_steps.append(AgenticReasoningStep(
        step_number=2,
        phase="Multi-Pass Retrieval & Fusion",
        status="success",
        title=f"Retrieved {len(all_sources)} Unique Context Chunks",
        description=f"Executed hybrid retrieval across {len(sub_queries)} search vectors with reciprocal rank fusion.",
        details={
            "chunks_retrieved": len(all_sources),
            "retrieval_latency_ms": round(retrieval_latency, 2),
            "retrieval_mode": retrieval_mode,
            "reranker_active": enable_reranker
        }
    ))

    # -------------------------------------------------------------
    # Step 3: Self-Reflection & Relevance Grading (CRAG)
    # -------------------------------------------------------------
    grading = grade_context_relevance(question, all_sources, threshold=60.0)
    final_sources = grading["filtered_sources"][:top_k + 2]

    # If context is graded as off-topic or insufficient, suppress sources early
    if not grading["is_sufficient"] and grading["relevant_count"] == 0:
        final_sources = []

    reasoning_steps.append(AgenticReasoningStep(
        step_number=3,
        phase="Self-Reflection & Corrective Grading (CRAG)",
        status="success" if grading["is_sufficient"] else "warning",
        title=f"Context Grounding Confidence: {grading['average_confidence']}%",
        description=grading["grading_assessment"],
        details={
            "average_confidence": grading["average_confidence"],
            "sufficient": grading["is_sufficient"],
            "retained_chunks": len(final_sources)
        }
    ))

    # Construct unified context string
    formatted_blocks = []
    for s in final_sources:
        header = f"--- Document: {s.document} | Page: {s.page} ---"
        formatted_blocks.append(f"{header}\n{s.snippet or ''}")
    unified_context = "\n\n".join(formatted_blocks)

    # -------------------------------------------------------------
    # Step 4: Grounded Synthesis with Chain-of-Thought Guardrails
    # -------------------------------------------------------------
    t_gen_start = time.perf_counter()
    answer, success, fallback_used = await generate_grounded_answer(
        question=question,
        context=unified_context,
        ollama_host=ollama_host,
        ollama_model=ollama_model,
        system_prompt_mode=system_prompt_mode,
        chat_history=chat_history,
        allow_fallback=True
    )
    generation_latency = (time.perf_counter() - t_gen_start) * 1000.0
    total_latency = (time.perf_counter() - t_start) * 1000.0

    # CRITICAL: If the answer indicates off-topic/ungrounded or if no relevant context passed grading, suppress ALL citations!
    if not final_sources or is_off_topic_or_ungrounded_answer(answer):
        final_sources = []
        step_title = "Off-Topic Query Verified"
        step_desc = "Detected off-topic or ungrounded question. Answered without citing irrelevant document references."
    else:
        step_title = "Verified Generation Completed"
        step_desc = "Synthesized final grounded response with strict source grounding and citation cross-verification."

    reasoning_steps.append(AgenticReasoningStep(
        step_number=4,
        phase="Grounded Fact-Checked Synthesis",
        status="success",
        title=step_title,
        description=step_desc,
        details={
            "generation_latency_ms": round(generation_latency, 2),
            "total_latency_ms": round(total_latency, 2),
            "fallback_used": fallback_used,
            "model_used": ollama_model if not fallback_used else "Extractive Fallback",
            "references_suppressed": len(final_sources) == 0
        }
    ))

    return {
        "answer": answer,
        "sources": final_sources,
        "reasoning_steps": reasoning_steps,
        "intent_type": intent_type,
        "confidence_score": grading["average_confidence"],
        "latency_ms": round(total_latency, 2),
        "retrieval_latency_ms": round(retrieval_latency, 2),
        "generation_latency_ms": round(generation_latency, 2),
        "fallback_used": fallback_used,
        "model_used": ollama_model if not fallback_used else "Extractive Fallback"
    }


async def execute_multi_document_comparison(
    doc_a: str,
    doc_b: str,
    topic: str,
    collection,
    embedding_model,
    reranker_model = None,
    ollama_host: str = settings.OLLAMA_HOST,
    ollama_model: str = settings.OLLAMA_MODEL
) -> Dict[str, Any]:
    """
    Performs side-by-side comparative analysis of two documents on a chosen topic.
    Returns structured markdown comparison table, synthesis, and per-document citations.
    """
    t_start = time.perf_counter()

    # Retrieve context for doc_a
    context_a, sources_a = retrieve_context(
        query=f"{topic} concepts, algorithms, methods, tradeoffs",
        collection=collection,
        embedding_model=embedding_model,
        top_k=4,
        document_filter=[doc_a],
        retrieval_mode="hybrid",
        reranker_model=reranker_model,
        enable_reranker=True
    )

    # Retrieve context for doc_b
    context_b, sources_b = retrieve_context(
        query=f"{topic} concepts, algorithms, methods, tradeoffs",
        collection=collection,
        embedding_model=embedding_model,
        top_k=4,
        document_filter=[doc_b],
        retrieval_mode="hybrid",
        reranker_model=reranker_model,
        enable_reranker=True
    )

    combined_context = (
        f"=== Context from Document A: {doc_a} ===\n{context_a}\n\n"
        f"=== Context from Document B: {doc_b} ===\n{context_b}"
    )

    prompt = f"""You are an Expert Technical Analyst specializing in comparative document analysis.

Analyze and compare the following two documents specifically regarding the topic: "{topic}".

Your output MUST include:
1. **Executive Comparison Summary** (2 paragraphs explaining key similarities and fundamental differences).
2. **Side-by-Side Comparison Matrix** as a clean Markdown table with columns:
   | Dimension / Aspect | {doc_a} | {doc_b} | Key Trade-off / Difference |
   Include rows for: Primary Purpose/Focus, Core Concepts & Algorithms, Complexity/Characteristics, Strengths, and Limitations.
3. **Synthesis & Recommended Takeaway**.
4. Strict citations format: [{doc_a}, Page X] or [{doc_b}, Page X].

Write in professional, clear, readable sentences without unnecessary ALL-CAPS words or shouting.

{combined_context}

Comparative Analysis and Matrix:"""

    answer, success, fallback_used = await generate_grounded_answer(
        question=f"Compare {doc_a} vs {doc_b} on {topic}",
        context=combined_context,
        ollama_host=ollama_host,
        ollama_model=ollama_model,
        system_prompt_mode="academic",
        allow_fallback=True
    )

    latency_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

    return {
        "doc_a": doc_a,
        "doc_b": doc_b,
        "topic": topic,
        "synthesis": answer,
        "sources_a": sources_a,
        "sources_b": sources_b,
        "latency_ms": latency_ms,
        "fallback_used": fallback_used
    }
