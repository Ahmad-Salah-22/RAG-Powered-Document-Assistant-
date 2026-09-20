from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.utils.logging_config import logger
from app.services.retrieval import load_embedding_model, get_chroma_collection
from app.api.routes.query import router as query_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager: Loads expensive resources ONCE at startup.
    - SentenceTransformer Embedding Model
    - ChromaDB Persistent Store & Collection
    """
    logger.info("=== Starting FastAPI Application Lifespan ===")
    
    # Load embedding model once
    try:
        app.state.embedding_model = load_embedding_model(settings.EMBEDDING_MODEL_NAME)
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}", exc_info=True)
        app.state.embedding_model = None

    # Load ChromaDB collection once
    try:
        app.state.chroma_collection = get_chroma_collection(
            chroma_path=settings.CHROMA_PATH,
            collection_name=settings.COLLECTION_NAME
        )
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB collection: {e}", exc_info=True)
        app.state.chroma_collection = None

    logger.info("=== Startup complete. Server ready to handle requests. ===")
    
    yield
    
    logger.info("=== Shutting down FastAPI application. Cleaning up resources. ===")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production RAG-Powered Document Assistant API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."}
    )

# Include Query API Router
app.include_router(query_router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs_url": "/docs",
        "health_check": "/health"
    }
