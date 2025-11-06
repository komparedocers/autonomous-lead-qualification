"""
Signals router - manage buying signals
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Signal, Company, User
from schemas import (
    SignalCreate,
    SignalResponse,
    SignalUpdate,
    SignalSearchRequest,
    SignalStatistics
)
from services.auth_service import get_current_user
from services.opensearch_service import opensearch_client
from services.kafka_service import kafka_producer
import structlog

logger = structlog.get_logger()

router = APIRouter()


@router.post("/", response_model=SignalResponse, status_code=status.HTTP_201_CREATED)
async def create_signal(
    signal_data: SignalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new signal"""
    # Verify company exists
    company = db.query(Company).filter(Company.id == signal_data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Create signal
    signal = Signal(
        company_id=signal_data.company_id,
        product_id=signal_data.product_id,
        kind=signal_data.kind,
        score=signal_data.score,
        confidence=signal_data.confidence,
        timestamp_start=signal_data.timestamp_start,
        timestamp_end=signal_data.timestamp_end,
        evidence=[e.dict() for e in signal_data.evidence],
        explanation=signal_data.explanation,
        features=signal_data.features,
        is_active=True,
        actioned=False
    )

    db.add(signal)
    db.commit()
    db.refresh(signal)

    # Index in OpenSearch
    await opensearch_client.index_document(
        "signals",
        signal.id,
        {
            "company_id": signal.company_id,
            "company_name": company.name,
            "product_id": signal.product_id,
            "kind": signal.kind.value,
            "score": signal.score,
            "confidence": signal.confidence,
            "timestamp_start": signal.timestamp_start.isoformat(),
            "explanation": signal.explanation,
            "evidence": signal.evidence,
            "is_active": signal.is_active,
            "actioned": signal.actioned
        }
    )

    # Publish to Kafka
    await kafka_producer.publish_signal({
        "signal_id": signal.id,
        "company_id": signal.company_id,
        "product_id": signal.product_id,
        "kind": signal.kind.value,
        "score": signal.score
    })

    logger.info("Signal created", signal_id=signal.id, company_id=signal.company_id)

    return signal


@router.get("/search", response_model=List[SignalResponse])
async def search_signals(
    query: Optional[str] = None,
    product_id: Optional[str] = None,
    kind: Optional[str] = None,
    min_score: float = Query(default=70, ge=0, le=100),
    is_active: Optional[bool] = True,
    actioned: Optional[bool] = None,
    limit: int = Query(default=50, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search signals with filters"""
    filters = {
        "query": query,
        "product_id": product_id,
        "kind": kind,
        "min_score": min_score,
        "is_active": is_active
    }

    # Search in OpenSearch
    results = await opensearch_client.search_signals(filters, size=limit, from_=offset)

    # Get signal IDs
    signal_ids = [int(hit["_id"]) for hit in results]

    # Fetch from database
    signals = db.query(Signal).filter(Signal.id.in_(signal_ids)).all()

    return signals


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get signal by ID"""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal


@router.patch("/{signal_id}", response_model=SignalResponse)
async def update_signal(
    signal_id: int,
    signal_update: SignalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update signal"""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    # Update fields
    update_data = signal_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(signal, field, value)

    db.commit()
    db.refresh(signal)

    logger.info("Signal updated", signal_id=signal_id)

    return signal


@router.get("/statistics/overview", response_model=SignalStatistics)
async def get_signal_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get signal statistics"""
    from sqlalchemy import func

    total_signals = db.query(func.count(Signal.id)).scalar()
    active_signals = db.query(func.count(Signal.id)).filter(Signal.is_active == True).scalar()
    signals_actioned = db.query(func.count(Signal.id)).filter(Signal.actioned == True).scalar()
    avg_score = db.query(func.avg(Signal.score)).filter(Signal.is_active == True).scalar() or 0

    # Signals by kind
    signals_by_kind = {}
    kind_counts = db.query(Signal.kind, func.count(Signal.id)).group_by(Signal.kind).all()
    for kind, count in kind_counts:
        signals_by_kind[kind.value] = count

    # Signals today
    from datetime import date
    today = datetime.combine(date.today(), datetime.min.time())
    signals_today = db.query(func.count(Signal.id)).filter(
        Signal.created_at >= today
    ).scalar()

    return SignalStatistics(
        total_signals=total_signals,
        active_signals=active_signals,
        signals_by_kind=signals_by_kind,
        avg_score=float(avg_score),
        signals_actioned=signals_actioned,
        signals_today=signals_today
    )


@router.post("/{signal_id}/action")
async def trigger_signal_action(
    signal_id: int,
    action_type: str = Query(..., description="Action type to trigger"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger action for signal"""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    # Publish action to Kafka
    await kafka_producer.publish_action({
        "signal_id": signal_id,
        "company_id": signal.company_id,
        "action_type": action_type,
        "product_id": signal.product_id,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Update signal
    signal.actioned = True
    signal.action_taken = action_type
    db.commit()

    logger.info("Signal action triggered", signal_id=signal_id, action=action_type)

    return {"status": "success", "signal_id": signal_id, "action": action_type}
