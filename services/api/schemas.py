"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import SignalKind, OutcomeStatus, ProposalStatus


# ============= User & Auth Schemas =============

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


# ============= Company Schemas =============

class CompanyBase(BaseModel):
    name: str
    domain: str
    country: Optional[str] = None
    region: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    size: Optional[str] = None
    employee_count: Optional[int] = None
    description: Optional[str] = None


class CompanyCreate(CompanyBase):
    tech_stack: Optional[List[str]] = []
    sources: Optional[List[Dict[str, Any]]] = []
    metadata: Optional[Dict[str, Any]] = {}


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    employee_count: Optional[int] = None
    tech_stack: Optional[List[str]] = None
    description: Optional[str] = None


class CompanyResponse(CompanyBase):
    id: int
    tech_stack: Optional[Dict] = None
    revenue: Optional[str] = None
    linkedin_url: Optional[str] = None
    founded_year: Optional[int] = None
    funding_stage: Optional[str] = None
    total_funding: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Company360(CompanyResponse):
    """Comprehensive company view with related data"""
    recent_signals: List["SignalResponse"] = []
    latest_events: List["EventResponse"] = []
    lead_scores: List["LeadScoreResponse"] = []
    proposals: List["ProposalResponse"] = []


# ============= Event Schemas =============

class EventBase(BaseModel):
    company_id: int
    event_type: str
    url: str
    title: Optional[str] = None
    text: Optional[str] = None


class EventCreate(EventBase):
    features: Optional[Dict[str, Any]] = {}
    language: Optional[str] = "en"
    timestamp: datetime
    source_type: str
    raw_data: Optional[Dict[str, Any]] = {}


class EventResponse(EventBase):
    id: int
    features: Optional[Dict] = None
    language: Optional[str] = None
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Signal Schemas =============

class Evidence(BaseModel):
    url: str
    snippet: str
    timestamp: datetime
    relevance_score: Optional[float] = None


class SignalBase(BaseModel):
    company_id: int
    product_id: str
    kind: SignalKind
    score: float = Field(ge=0, le=100)


class SignalCreate(SignalBase):
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    timestamp_start: datetime
    timestamp_end: Optional[datetime] = None
    evidence: List[Evidence]
    explanation: str
    features: Optional[Dict[str, Any]] = {}


class SignalUpdate(BaseModel):
    score: Optional[float] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    actioned: Optional[bool] = None
    action_taken: Optional[str] = None


class SignalResponse(SignalBase):
    id: int
    confidence: Optional[float] = None
    timestamp_start: datetime
    timestamp_end: Optional[datetime] = None
    evidence: List[Dict[str, Any]]
    explanation: str
    features: Optional[Dict] = None
    is_active: bool
    actioned: bool
    action_taken: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SignalSearchRequest(BaseModel):
    """Search filters for signals"""
    query: Optional[str] = None
    product_id: Optional[str] = None
    kind: Optional[SignalKind] = None
    min_score: float = Field(default=70, ge=0, le=100)
    is_active: Optional[bool] = True
    actioned: Optional[bool] = None
    company_ids: Optional[List[int]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, le=1000)
    offset: int = Field(default=0, ge=0)


# ============= Lead Score Schemas =============

class LeadScoreBase(BaseModel):
    company_id: int
    product_id: str
    score: float = Field(ge=0, le=100)


class LeadScoreCreate(LeadScoreBase):
    fit_score: float = Field(ge=0, le=100)
    intent_score: float = Field(ge=0, le=100)
    timing_score: float = Field(ge=0, le=100)
    components: Dict[str, Any]
    framework_data: Optional[Dict[str, Any]] = {}


class LeadScoreResponse(LeadScoreBase):
    id: int
    fit_score: Optional[float] = None
    intent_score: Optional[float] = None
    timing_score: Optional[float] = None
    bant_qualified: Optional[bool] = None
    champ_qualified: Optional[bool] = None
    meddicc_qualified: Optional[bool] = None
    components: Optional[Dict] = None
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= Proposal Schemas =============

class ProposalBase(BaseModel):
    company_id: int
    product_id: str
    title: str


class ProposalCreate(ProposalBase):
    outline_markdown: Optional[str] = None
    evidence_used: Optional[List[int]] = []  # Signal IDs


class ProposalUpdate(BaseModel):
    title: Optional[str] = None
    outline_markdown: Optional[str] = None
    content_markdown: Optional[str] = None
    status: Optional[ProposalStatus] = None


class ProposalResponse(ProposalBase):
    id: int
    outline_markdown: Optional[str] = None
    content_markdown: Optional[str] = None
    pdf_uri: Optional[str] = None
    status: ProposalStatus
    version: int
    generated_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============= Feedback Schemas =============

class FeedbackBase(BaseModel):
    signal_id: int
    outcome: OutcomeStatus


class FeedbackCreate(FeedbackBase):
    reason: Optional[str] = None
    deal_value: Optional[float] = None
    time_to_close: Optional[int] = None


class FeedbackResponse(FeedbackBase):
    id: int
    reason: Optional[str] = None
    deal_value: Optional[float] = None
    time_to_close: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Agent Schemas =============

class AgentRunRequest(BaseModel):
    """Request to run an agent"""
    agent_name: str
    agent_type: str
    company_id: Optional[int] = None
    playbook: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = {}


class AgentRunResponse(BaseModel):
    id: int
    agent_name: str
    agent_type: str
    status: str
    output_data: Optional[Dict] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============= Webhook & Integration Schemas =============

class WebhookEvent(BaseModel):
    """Generic webhook event"""
    source: str
    event_type: str
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None


class CRMIntegrationRequest(BaseModel):
    """CRM integration configuration"""
    crm_type: str  # salesforce, hubspot
    credentials: Dict[str, str]
    field_mapping: Optional[Dict[str, str]] = {}


# ============= Statistics & Analytics Schemas =============

class SignalStatistics(BaseModel):
    """Signal statistics"""
    total_signals: int
    active_signals: int
    signals_by_kind: Dict[str, int]
    avg_score: float
    signals_actioned: int
    signals_today: int


class DashboardMetrics(BaseModel):
    """Dashboard overview metrics"""
    total_companies: int
    total_signals: int
    total_proposals: int
    high_score_leads: int
    signals_today: int
    win_rate: float
    avg_deal_value: float


# Forward references resolution
Company360.model_rebuild()
