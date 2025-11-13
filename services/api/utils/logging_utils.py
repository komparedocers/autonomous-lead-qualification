"""
Logging utilities for consistent logging across the application
"""
from fastapi import Request
from typing import Optional, Dict, Any
import structlog
from functools import wraps
import time

logger = structlog.get_logger()


def get_request_context(request: Request) -> Dict[str, Any]:
    """Extract request context for logging"""
    return {
        "request_id": getattr(request.state, "request_id", "unknown"),
        "method": request.method,
        "path": str(request.url),
        "client_host": request.client.host if request.client else "unknown"
    }


def log_operation(operation_name: str):
    """
    Decorator for logging function operations with timing
    Usage:
        @log_operation("create_company")
        async def create_company(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            func_logger = structlog.get_logger().bind(operation=operation_name)

            # Extract request if available
            request = kwargs.get('request') or next((arg for arg in args if isinstance(arg, Request)), None)
            context = get_request_context(request) if request else {}

            func_logger.info(
                f"{operation_name}_started",
                **context
            )

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                func_logger.info(
                    f"{operation_name}_completed",
                    duration_seconds=round(duration, 3),
                    **context
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                func_logger.error(
                    f"{operation_name}_failed",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    duration_seconds=round(duration, 3),
                    **context,
                    exc_info=True
                )
                raise

        return wrapper
    return decorator


def log_database_operation(operation: str, table: str, record_id: Optional[int] = None):
    """Log database operations"""
    log_data = {
        "operation": operation,
        "table": table
    }
    if record_id:
        log_data["record_id"] = record_id

    logger.debug("database_operation", **log_data)


def log_external_api_call(service: str, endpoint: str, duration: float, success: bool):
    """Log external API calls"""
    logger.info(
        "external_api_call",
        service=service,
        endpoint=endpoint,
        duration_seconds=round(duration, 3),
        success=success
    )


def log_agent_action(agent_name: str, action: str, details: Dict[str, Any]):
    """Log AI agent actions"""
    logger.info(
        "agent_action",
        agent=agent_name,
        action=action,
        **details
    )
