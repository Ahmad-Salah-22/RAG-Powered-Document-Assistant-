import httpx
from typing import Tuple
from app.utils.logging_config import logger
from app.core.config import settings

SYSTEM_RAG_PROMPT = """You are a strictly document-grounded AI assistant.

Your task is to answer the user's question using ONLY the provided document context blocks below.

STRICT GROUNDING RULES:
1. Base your answer ENTIRELY on the provided context.
2. If the context does not contain enough information to answer the question, state clearly: "I could not find this information in the provided documents."
3. Do NOT make up facts, hallucinate, or extrapolate beyond the provided text.
4. Always cite your sources in your answer using format: [Document Name, Page X].
5. Keep your response concise, clear, and well-structured.

CONTEXT BLOCKS:
{context}

USER QUESTION:
{question}

GROUNDED ANSWER WITH CITATIONS:"""


async def check_ollama_availability(ollama_host: str = settings.OLLAMA_HOST) -> bool:
    """
    Checks if local Ollama daemon is active and responsive.
    """
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{ollama_host}/api/tags")
            return resp.status_code == 200
    except Exception as e:
        logger.debug(f"Ollama health check ping failed: {e}")
        return False


async def generate_grounded_answer(
    question: str,
    context: str,
    ollama_host: str = settings.OLLAMA_HOST,
    ollama_model: str = settings.OLLAMA_MODEL,
    timeout: float = settings.OLLAMA_TIMEOUT
) -> Tuple[str, bool]:
    """
    Invokes Ollama local LLM to generate grounded answer from context.

    Returns:
        Tuple[str, bool]: (Answer text, Success flag)
    """
    if not context or not context.strip():
        logger.info("Empty context provided to generation service. Returning ungrounded fallback.")
        return (
            "I could not find relevant information in the provided documents to answer your question.",
            True
        )

    prompt = SYSTEM_RAG_PROMPT.format(context=context, question=question)

    logger.info(f"Sending prompt to Ollama LLM model '{ollama_model}' at '{ollama_host}'")

    payload = {
        "model": ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for factual grounding
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
                return answer_text, True
            elif response.status_code == 404:
                error_msg = f"Ollama model '{ollama_model}' not found. Please run 'ollama pull {ollama_model}'."
                logger.error(error_msg)
                return f"Error: {error_msg}", False
            else:
                error_msg = f"Ollama HTTP {response.status_code}: {response.text}"
                logger.error(error_msg)
                return f"Error connecting to LLM service: {error_msg}", False

    except httpx.ConnectError:
        error_msg = (
            f"Unable to connect to Ollama service at {ollama_host}. "
            f"Please make sure Ollama is running ('ollama serve')."
        )
        logger.error(error_msg)
        return f"Service Unavailable: {error_msg}", False
    except httpx.TimeoutException:
        error_msg = f"Request to Ollama timed out after {timeout} seconds."
        logger.error(error_msg)
        return f"Timeout Error: {error_msg}", False
    except Exception as e:
        error_msg = f"Unexpected error during generation: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"Error: {error_msg}", False
