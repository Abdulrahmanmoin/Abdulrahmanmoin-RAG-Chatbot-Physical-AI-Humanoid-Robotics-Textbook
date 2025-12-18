from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
import logging
import traceback

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        try:
            response = await call_next(request)
            return response
        except StarletteHTTPException as e:
            # Handle FastAPI HTTP exceptions
            logger.warning(f"HTTP Exception: {e.status_code} - {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail, "error_code": f"HTTP_{e.status_code}"}
            )
        except RequestValidationError as e:
            # Handle validation errors
            logger.warning(f"Validation Error: {e.errors()}")
            return JSONResponse(
                status_code=422,
                content={
                    "error": "Validation error",
                    "details": e.errors(),
                    "error_code": "VALIDATION_ERROR"
                }
            )
        except Exception as e:
            # Handle all other exceptions
            error_id = f"ERR_{id(e)}"
            logger.error(f"Unhandled Exception {error_id}: {str(e)}", exc_info=True)

            # In production, don't expose internal error details
            error_detail = "Internal server error" if request.app.debug else "An error occurred"

            return JSONResponse(
                status_code=500,
                content={
                    "error": error_detail,
                    "error_code": "INTERNAL_ERROR",
                    "error_id": error_id
                }
            )