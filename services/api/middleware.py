"""
Logging middleware for request tracking and comprehensive logging
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
from typing import Callable
import structlog

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging with correlation IDs"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())

        # Add to request state for access in handlers
        request.state.request_id = request_id

        # Start timer
        start_time = time.time()

        # Extract request details
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)

        # Log incoming request
        logger.info(
            "incoming_request",
            request_id=request_id,
            method=method,
            path=path,
            client_host=client_host,
            query_params=query_params,
            user_agent=request.headers.get("user-agent", "unknown")
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log successful response
            logger.info(
                "request_completed",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                duration_seconds=round(duration, 3),
                client_host=client_host
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Log error
            logger.error(
                "request_failed",
                request_id=request_id,
                method=method,
                path=path,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_seconds=round(duration, 3),
                client_host=client_host,
                exc_info=True
            )

            # Re-raise to let error handler deal with it
            raise


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for catching and logging unhandled errors"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")

            logger.exception(
                "unhandled_exception",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error_type=type(e).__name__,
                error_message=str(e),
                client_host=request.client.host if request.client else "unknown",
                exc_info=True
            )

            raise
