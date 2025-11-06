"""
Feedback router - track sales outcomes for learning
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Feedback, Signal, User
from schemas import FeedbackCreate, FeedbackResponse
from services.auth_service import get_current_user
import structlog

logger = structlog.get_logger()

router = APIRouter()


@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit feedback for a signal (won, lost, ignored)"""
    # Verify signal exists
    signal = db.query(Signal).filter(Signal.id == feedback_data.signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    # Check if feedback already exists
    existing = db.query(Feedback).filter(
        Feedback.signal_id == feedback_data.signal_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Feedback already exists for this signal")

    # Create feedback
    feedback = Feedback(
        signal_id=feedback_data.signal_id,
        outcome=feedback_data.outcome,
        reason=feedback_data.reason,
        deal_value=feedback_data.deal_value,
        time_to_close=feedback_data.time_to_close,
        user_id=current_user.id
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    logger.info(
        "Feedback submitted",
        signal_id=feedback_data.signal_id,
        outcome=feedback_data.outcome.value,
        user=current_user.username
    )

    # Trigger model retraining if needed
    # This would be handled by the workers service

    return feedback


@router.get("/signal/{signal_id}", response_model=FeedbackResponse)
async def get_signal_feedback(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get feedback for a signal"""
    feedback = db.query(Feedback).filter(Feedback.signal_id == signal_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback


@router.get("/", response_model=List[FeedbackResponse])
async def list_feedback(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all feedback"""
    feedback = db.query(Feedback).order_by(
        Feedback.created_at.desc()
    ).offset(skip).limit(limit).all()
    return feedback
