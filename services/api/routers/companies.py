"""
Companies router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import Company, Signal, Event, LeadScore, User
from schemas import CompanyCreate, CompanyResponse, CompanyUpdate, Company360
from services.auth_service import get_current_user
from services.opensearch_service import opensearch_client
from services.neo4j_service import neo4j_driver

router = APIRouter()


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new company"""
    existing = db.query(Company).filter(Company.domain == company_data.domain).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company with this domain already exists")

    company = Company(**company_data.dict())
    db.add(company)
    db.commit()
    db.refresh(company)

    # Create in Neo4j
    await neo4j_driver.create_company_node({
        "company_id": company.id,
        "name": company.name,
        "domain": company.domain,
        "industry": company.industry,
        "country": company.country,
        "size": company.size
    })

    # Index in OpenSearch
    await opensearch_client.index_document("companies", company.id, {
        "company_id": company.id,
        "name": company.name,
        "domain": company.domain,
        "country": company.country,
        "industry": company.industry,
        "sector": company.sector,
        "size": company.size,
        "description": company.description,
        "tech_stack": company.tech_stack
    })

    return company


@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=1000),
    industry: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List companies with filters"""
    query = db.query(Company)

    if industry:
        query = query.filter(Company.industry == industry)
    if country:
        query = query.filter(Company.country == country)

    companies = query.offset(skip).limit(limit).all()
    return companies


@router.get("/{company_id}", response_model=Company360)
async def get_company_360(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive company view (Company 360)"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get related data
    recent_signals = db.query(Signal).filter(
        Signal.company_id == company_id,
        Signal.is_active == True
    ).order_by(Signal.timestamp_start.desc()).limit(10).all()

    latest_events = db.query(Event).filter(
        Event.company_id == company_id
    ).order_by(Event.timestamp.desc()).limit(20).all()

    lead_scores = db.query(LeadScore).filter(
        LeadScore.company_id == company_id
    ).all()

    return Company360(
        **company.__dict__,
        recent_signals=recent_signals,
        latest_events=latest_events,
        lead_scores=lead_scores,
        proposals=[]
    )


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_update: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update company"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_data = company_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    db.commit()
    db.refresh(company)

    return company


@router.get("/{company_id}/similar", response_model=List[CompanyResponse])
async def find_similar_companies(
    company_id: int,
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Find similar companies based on characteristics"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Use Neo4j to find similar companies
    similar = await neo4j_driver.find_similar_companies(company_id, limit=limit)

    # Get company details
    similar_ids = [s["similar"]["company_id"] for s in similar]
    companies = db.query(Company).filter(Company.id.in_(similar_ids)).all()

    return companies
