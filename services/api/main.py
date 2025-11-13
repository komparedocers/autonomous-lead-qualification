"""
Main FastAPI application for Lead Qualification Platform
"""
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import sys
from prometheus_client import make_asgi_app

from config import settings
from database import engine, Base, get_db
from routers import signals, companies, proposals, agents, integrations, auth, feedback
from services.kafka_service import kafka_producer
from services.opensearch_service import opensearch_client
from services.neo4j_service import neo4j_driver
from services.minio_service import minio_client
from middleware import RequestLoggingMiddleware, ErrorLoggingMiddleware

# Configure comprehensive structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events"""
    # Startup
    logger.info("Starting Lead Qualification Platform API")

    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Initialize Kafka topics
    try:
        await kafka_producer.start()
        logger.info("Kafka producer initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka: {e}")

    # Initialize OpenSearch indices
    try:
        await opensearch_client.initialize_indices()
        logger.info("OpenSearch indices initialized")
    except Exception as e:
        logger.error(f"Failed to initialize OpenSearch: {e}")

    # Initialize MinIO buckets
    try:
        await minio_client.initialize_buckets()
        logger.info("MinIO buckets initialized")
    except Exception as e:
        logger.error(f"Failed to initialize MinIO: {e}")

    logger.info("API startup complete")

    yield

    # Shutdown
    logger.info("Shutting down API")
    await kafka_producer.stop()
    neo4j_driver.close()
    logger.info("API shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="Lead Qualification Platform API",
    description="Agentic AI-based real-time sales lead qualification platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add logging middleware (first to catch all requests)
app.add_middleware(ErrorLoggingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],  # Expose request ID to frontend
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["signals"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(proposals.router, prefix="/api/v1/proposals", tags=["proposals"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Lead Qualification Platform API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "services": {}
    }

    # Check database
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        from services.redis_service import redis_client
        redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check OpenSearch
    try:
        opensearch_client.client.cluster.health()
        health_status["services"]["opensearch"] = "healthy"
    except Exception as e:
        health_status["services"]["opensearch"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Neo4j
    try:
        neo4j_driver.verify_connectivity()
        health_status["services"]["neo4j"] = "healthy"
    except Exception as e:
        health_status["services"]["neo4j"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    return health_status


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with comprehensive logging"""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        "global_exception_handler",
        request_id=request_id,
        method=request.method,
        path=str(request.url),
        error_type=type(exc).__name__,
        error_message=str(exc),
        client_host=request.client.host if request.client else "unknown",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "request_id": request_id,
            "error_type": type(exc).__name__
        },
        headers={"X-Request-ID": request_id}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler with logging"""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        "http_exception",
        request_id=request_id,
        method=request.method,
        path=str(request.url),
        status_code=exc.status_code,
        detail=exc.detail,
        client_host=request.client.host if request.client else "unknown"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": request_id
        },
        headers={"X-Request-ID": request_id}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
