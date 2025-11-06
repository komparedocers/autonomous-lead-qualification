"""
Database models for Lead Qualification Platform
"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, JSON,
    ForeignKey, Enum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from database import Base


class SignalKind(str, enum.Enum):
    """Signal type enumeration"""
    HIRING_SPIKE = "hiring_spike"
    TECH_ADOPTION = "tech_adoption"
    FUNDING_EVENT = "funding_event"
    COMPLIANCE_WIN = "compliance_win"
    EXPANSION = "expansion"
    PRODUCT_LAUNCH = "product_launch"
    LEADERSHIP_CHANGE = "leadership_change"
    BUDGET_EVENT = "budget_event"
    PARTNERSHIP = "partnership"
    PAIN_POINT = "pain_point"


class OutcomeStatus(str, enum.Enum):
    """Outcome status for feedback"""
    WON = "won"
    LOST = "lost"
    IGNORED = "ignored"
    IN_PROGRESS = "in_progress"


class ProposalStatus(str, enum.Enum):
    """Proposal status"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Company(Base):
    """Company entity model"""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    domain = Column(String(255), unique=True, index=True, nullable=False)
    country = Column(String(100), index=True)
    region = Column(String(100))
    industry = Column(String(200), index=True)
    sector = Column(String(200))
    size = Column(String(50))  # e.g., "50-200", "1000+"
    employee_count = Column(Integer)
    revenue = Column(String(100))
    tech_stack = Column(JSON)  # List of technologies
    description = Column(Text)
    linkedin_url = Column(String(500))
    twitter_handle = Column(String(100))
    founded_year = Column(Integer)
    funding_stage = Column(String(100))
    total_funding = Column(Float)
    last_funding_date = Column(DateTime(timezone=True))
    sources = Column(JSON)  # List of data sources
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    events = relationship("Event", back_populates="company", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="company", cascade="all, delete-orphan")
    lead_scores = relationship("LeadScore", back_populates="company", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="company", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_company_industry_size", "industry", "size"),
        Index("idx_company_country_sector", "country", "sector"),
    )


class Event(Base):
    """Event entity - represents raw data captured from sources"""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # job_posting, news, blog, etc.
    url = Column(String(2000), nullable=False)
    title = Column(String(1000))
    text = Column(Text)
    features = Column(JSON)  # Extracted features
    language = Column(String(10))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    source_type = Column(String(100))  # web, api, webhook, etc.
    raw_data = Column(JSON)
    embedding_vector = Column(JSON)  # For similarity search
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company = relationship("Company", back_populates="events")

    __table_args__ = (
        Index("idx_event_company_time", "company_id", "timestamp"),
        Index("idx_event_type_time", "event_type", "timestamp"),
    )


class Signal(Base):
    """Signal entity - qualified buying signals"""
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    product_id = Column(String(100), index=True)  # Which product this signal is for
    kind = Column(Enum(SignalKind), nullable=False, index=True)
    score = Column(Float, nullable=False, index=True)  # 0-100 score
    confidence = Column(Float)  # 0-1 confidence
    timestamp_start = Column(DateTime(timezone=True), nullable=False, index=True)
    timestamp_end = Column(DateTime(timezone=True))
    evidence = Column(JSON, nullable=False)  # List of {url, snippet, timestamp}
    explanation = Column(Text)  # Human-readable explanation
    features = Column(JSON)  # Features used for scoring
    metadata = Column(JSON)
    is_active = Column(Boolean, default=True, index=True)
    actioned = Column(Boolean, default=False)
    action_taken = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="signals")
    feedback = relationship("Feedback", back_populates="signal", uselist=False)

    __table_args__ = (
        Index("idx_signal_score_active", "score", "is_active"),
        Index("idx_signal_company_product", "company_id", "product_id"),
        Index("idx_signal_kind_time", "kind", "timestamp_start"),
    )


class LeadScore(Base):
    """Lead scoring model - composite score per company/product"""
    __tablename__ = "lead_scores"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    product_id = Column(String(100), nullable=False, index=True)
    score = Column(Float, nullable=False, index=True)  # 0-100 overall score
    fit_score = Column(Float)  # ICP fit component
    intent_score = Column(Float)  # Intent signals component
    timing_score = Column(Float)  # Timing/velocity component
    components = Column(JSON)  # Detailed breakdown
    bant_qualified = Column(Boolean)  # Budget, Authority, Need, Timeline
    champ_qualified = Column(Boolean)  # Challenges, Authority, Money, Prioritization
    meddicc_qualified = Column(Boolean)  # Metrics, Buyer, Decision, Process, etc.
    framework_data = Column(JSON)  # BANT/CHAMP/MEDDICC field values
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="lead_scores")

    __table_args__ = (
        UniqueConstraint("company_id", "product_id", name="uq_company_product"),
        Index("idx_lead_score_product", "product_id", "score"),
    )


class Proposal(Base):
    """Proposal entity - AI-generated proposals"""
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    product_id = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    outline_markdown = Column(Text)
    content_markdown = Column(Text)
    pdf_uri = Column(String(1000))  # MinIO URI
    status = Column(Enum(ProposalStatus), default=ProposalStatus.DRAFT, index=True)
    version = Column(Integer, default=1)
    evidence_used = Column(JSON)  # References to signals/events
    generated_by = Column(String(100))  # agent or user
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    sent_at = Column(DateTime(timezone=True))
    opened_at = Column(DateTime(timezone=True))
    responded_at = Column(DateTime(timezone=True))
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="proposals")

    __table_args__ = (
        Index("idx_proposal_company_product", "company_id", "product_id"),
        Index("idx_proposal_status", "status"),
    )


class Feedback(Base):
    """Feedback entity - sales outcomes for learning"""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False, index=True)
    outcome = Column(Enum(OutcomeStatus), nullable=False, index=True)
    reason = Column(Text)
    deal_value = Column(Float)  # Actual deal value if won
    time_to_close = Column(Integer)  # Days from signal to close
    user_id = Column(Integer, ForeignKey("users.id"))
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    signal = relationship("Signal", back_populates="feedback")

    __table_args__ = (
        Index("idx_feedback_outcome", "outcome", "created_at"),
    )


class AgentRun(Base):
    """Agent execution tracking"""
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(200), nullable=False, index=True)
    agent_type = Column(String(100))  # discoverer, enricher, scorer, proposer, etc.
    company_id = Column(Integer, ForeignKey("companies.id"))
    playbook = Column(String(200))
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(String(50), index=True)  # running, completed, failed
    error_message = Column(Text)
    duration_seconds = Column(Float)
    cost = Column(Float)  # LLM API cost
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_agent_run_status", "status", "started_at"),
        Index("idx_agent_run_type", "agent_type", "started_at"),
    )


class CrawlJob(Base):
    """Crawler job tracking"""
    __tablename__ = "crawl_jobs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    url = Column(String(2000), nullable=False)
    job_type = Column(String(100))  # sitemap, careers, blog, etc.
    status = Column(String(50), index=True)  # pending, running, completed, failed
    pages_crawled = Column(Integer, default=0)
    events_created = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_crawl_job_status", "status", "started_at"),
    )
