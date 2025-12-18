from fastapi import APIRouter
from typing import Dict, Any
import time
from ...config.database import engine
from ...config.vector_store import vector_store
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check endpoint
    """
    start_time = time.time()

    checks = {
        "database": "unknown",
        "vector_store": "unknown",
        "api": "healthy"
    }

    # Check database connection
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = "error"

    # Check vector store connection
    try:
        # Simple check to see if we can access the collection
        client = vector_store.get_client()
        collections = client.get_collections()
        checks["vector_store"] = "ok"
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        checks["vector_store"] = "error"

    # Overall status
    overall_status = "healthy" if all(v == "ok" for v in checks.values() if v != "api") else "degraded"

    response = {
        "status": overall_status,
        "checks": checks,
        "timestamp": time.time(),
        "response_time_ms": round((time.time() - start_time) * 1000, 2)
    }

    return response

@router.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Readiness check - indicates if the service is ready to accept traffic
    """
    # For now, just return that we're ready
    # In a more complex system, you might check if all required services are available
    return {"status": "ready"}