from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, pipeline, projection, enrichment
from app.exceptions.handlers import register_exception_handlers
from app.config.settings import settings
from app.logging.logger import logger

def create_app() -> FastAPI:
    """
    Initializes and configures the FastAPI application instance.
    """
    logger.info("Bootstrapping CandidateCore Engine API Server...")
    
    app = FastAPI(
        title=settings.app_name,
        description="Deterministic Candidate Canonicalization Engine for Eightfold Ingestion Pipeline",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Configure CORS for frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Set restrictively in production environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API Route Routers
    app.include_router(health.router)
    app.include_router(pipeline.router)
    app.include_router(projection.router)
    app.include_router(enrichment.router)

    # Register Centralized Error Handling Middlewares
    register_exception_handlers(app)

    logger.info("CandidateCore Engine API Server successfully initialized.")
    return app

app = create_app()
