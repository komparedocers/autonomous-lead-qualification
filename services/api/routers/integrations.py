"""
Integrations router - CRM and external system integrations
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from database import get_db
from models import User
from schemas import WebhookEvent, CRMIntegrationRequest
from services.auth_service import get_current_user
from services.kafka_service import kafka_producer
import structlog

logger = structlog.get_logger()

router = APIRouter()


@router.post("/webhook")
async def receive_webhook(
    event: WebhookEvent,
    db: Session = Depends(get_db)
):
    """Receive webhook events from external systems"""
    logger.info("Webhook received", source=event.source, type=event.event_type)

    # Publish to Kafka
    await kafka_producer.publish_event(
        event_type=f"webhook.{event.source}.{event.event_type}",
        data=event.dict()
    )

    return {"status": "received", "event_id": event.source}


@router.post("/crm/configure")
async def configure_crm_integration(
    config: CRMIntegrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Configure CRM integration"""
    # Store CRM configuration (encrypted credentials)
    # This is simplified - production would encrypt credentials
    logger.info("CRM integration configured", crm=config.crm_type, user=current_user.username)

    return {"status": "configured", "crm_type": config.crm_type}


@router.post("/crm/{crm_type}/sync")
async def sync_with_crm(
    crm_type: str,
    direction: str = "bidirectional",
    current_user: User = Depends(get_current_user)
):
    """Trigger CRM sync"""
    # Publish sync action
    await kafka_producer.publish(
        "actions.triggered",
        {
            "action_type": "crm_sync",
            "crm_type": crm_type,
            "direction": direction,
            "user_id": current_user.id
        }
    )

    return {"status": "sync_initiated", "crm": crm_type}
