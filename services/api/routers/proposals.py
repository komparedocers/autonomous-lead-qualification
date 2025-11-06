"""
Proposals router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Proposal, Company, User
from schemas import ProposalCreate, ProposalResponse, ProposalUpdate
from services.auth_service import get_current_user

router = APIRouter()


@router.post("/", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    proposal_data: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new proposal"""
    company = db.query(Company).filter(Company.id == proposal_data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    proposal = Proposal(
        company_id=proposal_data.company_id,
        product_id=proposal_data.product_id,
        title=proposal_data.title,
        outline_markdown=proposal_data.outline_markdown,
        evidence_used=proposal_data.evidence_used,
        generated_by="user",
        reviewed_by=current_user.id
    )

    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    return proposal


@router.get("/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get proposal by ID"""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@router.patch("/{proposal_id}", response_model=ProposalResponse)
async def update_proposal(
    proposal_id: int,
    proposal_update: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update proposal"""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    update_data = proposal_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(proposal, field, value)

    db.commit()
    db.refresh(proposal)

    return proposal


@router.post("/draft", response_model=ProposalResponse)
async def draft_proposal(
    company_id: int,
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Auto-generate proposal draft using AI"""
    # This will trigger the proposal generation agent
    from services.kafka_service import kafka_producer

    await kafka_producer.publish(
        "actions.triggered",
        {
            "action_type": "generate_proposal",
            "company_id": company_id,
            "product_id": product_id,
            "user_id": current_user.id
        }
    )

    return {"status": "generating", "message": "Proposal generation initiated"}
