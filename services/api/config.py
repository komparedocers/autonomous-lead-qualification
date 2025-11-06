"""
Configuration settings for the API service
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Lead Qualification Platform"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://app:app_password_123@db:5432/leadqualification"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # Kafka
    KAFKA_BROKERS: str = os.getenv("KAFKA_BROKERS", "redpanda:9092")
    KAFKA_TOPICS: dict = {
        "raw_events": "raw.events",
        "clean_events": "clean.events",
        "companies_updates": "companies.updates",
        "signals_detected": "signals.detected",
        "actions_triggered": "actions.triggered"
    }

    # OpenSearch
    OPENSEARCH_URL: str = os.getenv("OPENSEARCH_URL", "http://opensearch:9200")

    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password123")

    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "admin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "admin_password_123")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "False").lower() == "true"
    MINIO_BUCKETS: List[str] = [
        "raw-html",
        "screenshots",
        "proposals",
        "pdfs",
        "artifacts"
    ]

    # JWT Authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24  # 24 hours

    # AI Models
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DEFAULT_LLM: str = "openai"  # or "anthropic"
    DEFAULT_MODEL: str = "gpt-4-turbo-preview"  # or "claude-3-sonnet-20240229"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://web:3000"
    ]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Crawler Settings
    CRAWLER_USER_AGENT: str = "LeadQualificationBot/1.0 (polite crawler)"
    CRAWLER_RESPECT_ROBOTS_TXT: bool = True
    CRAWLER_DELAY_SECONDS: float = 1.0
    CRAWLER_MAX_CONCURRENT: int = 10

    # Signal Scoring
    SIGNAL_SCORE_THRESHOLD: int = 70
    SIGNAL_FIT_WEIGHT: float = 0.4
    SIGNAL_INTENT_WEIGHT: float = 0.4
    SIGNAL_TIMING_WEIGHT: float = 0.2

    # Proposal Generation
    PROPOSAL_MAX_LENGTH: int = 5000
    PROPOSAL_TEMPLATE_PATH: str = "./templates/proposals"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
