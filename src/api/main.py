from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat, health
from ..config.settings import settings
from .middleware.logging import LoggingMiddleware
from .middleware.error_handler import ErrorHandlerMiddleware
import logging
import sys

# Configure logging
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title=settings.app_name,
    description="RAG Chatbot API for the Physical AI & Humanoid Robotics Book",
    version=settings.app_version,
    debug=settings.debug,
    openapi_url="/api/openapi.json" if settings.app_env != "production" else None,
    docs_url="/api/docs" if settings.app_env != "production" else None,
    redoc_url="/api/redoc" if settings.app_env != "production" else None,
)

# Add custom middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Expose custom headers if needed
    # expose_headers=["Access-Control-Allow-Origin"]
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(health.router, prefix="/api", tags=["health"])

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up RAG Chatbot API")
    # Any startup tasks can go here

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down RAG Chatbot API")
    # Any cleanup tasks can go here

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "RAG Chatbot API for Physical AI & Humanoid Robotics Book",
        "version": settings.app_version,
        "status": "running"
    }

logger.info("FastAPI app initialized with CORS and routers")