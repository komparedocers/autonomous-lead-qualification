"""
Agents router - manage AI agent execution
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import AgentRun, User
from schemas import AgentRunRequest, AgentRunResponse
from services.auth_service import get_current_user
from services.kafka_service import kafka_producer

router = APIRouter()


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    agent_request: AgentRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run an agent playbook"""
    # Create agent run record
    agent_run = AgentRun(
        agent_name=agent_request.agent_name,
        agent_type=agent_request.agent_type,
        company_id=agent_request.company_id,
        playbook=agent_request.playbook,
        input_data=agent_request.input_data,
        status="pending"
    )

    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    # Publish to Kafka for worker processing
    await kafka_producer.publish(
        "actions.triggered",
        {
            "action_type": "run_agent",
            "agent_run_id": agent_run.id,
            "agent_name": agent_request.agent_name,
            "agent_type": agent_request.agent_type,
            "company_id": agent_request.company_id,
            "input_data": agent_request.input_data
        }
    )

    return agent_run


@router.get("/{agent_run_id}", response_model=AgentRunResponse)
async def get_agent_run(
    agent_run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get agent run status and results"""
    agent_run = db.query(AgentRun).filter(AgentRun.id == agent_run_id).first()
    if not agent_run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return agent_run


@router.get("/", response_model=List[AgentRunResponse])
async def list_agent_runs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List recent agent runs"""
    agent_runs = db.query(AgentRun).order_by(
        AgentRun.started_at.desc()
    ).offset(skip).limit(limit).all()
    return agent_runs
