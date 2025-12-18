from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
import time
import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate a unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to request state for access in other parts of the app
        request.state.request_id = request_id

        start_time = time.time()

        # Log request
        logger.info(
            f"Request ID: {request_id} | "
            f"Method: {request.method} | "
            f"Path: {request.url.path} | "
            f"IP: {self.get_client_ip(request)} | "
            f"User-Agent: {request.headers.get('user-agent', 'Unknown')}"
        )

        try:
            response = await call_next(request)
        except Exception as e:
            # Log exceptions
            logger.error(
                f"Request ID: {request_id} | "
                f"Error: {str(e)} | "
                f"Path: {request.url.path}",
                exc_info=True
            )
            raise
        finally:
            # Calculate response time
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Request ID: {request_id} | "
                f"Status: {response.status_code} | "
                f"Process Time: {process_time:.2f}s | "
                f"Path: {request.url.path}"
            )

        return response

    def get_client_ip(self, request: Request) -> str:
        # Try to get the real client IP from headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0]

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host