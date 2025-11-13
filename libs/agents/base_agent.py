"""
Base agent class for all AI agents
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import structlog
import uuid

logger = structlog.get_logger()


@dataclass
class AgentState:
    """State container for agent execution"""
    execution_id: Optional[str] = None
    company_id: Optional[int] = None
    company_data: Optional[Dict[str, Any]] = None
    signals: List[Dict[str, Any]] = None
    events: List[Dict[str, Any]] = None
    scores: Dict[str, float] = None
    proposal: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.execution_id is None:
            self.execution_id = str(uuid.uuid4())
        if self.signals is None:
            self.signals = []
        if self.events is None:
            self.events = []
        if self.scores is None:
            self.scores = {}
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class BaseAgent:
    """Base class for all agents"""

    def __init__(self, name: str, agent_type: str):
        self.name = name
        self.agent_type = agent_type
        self.logger = structlog.get_logger().bind(agent=name)

    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute agent logic
        Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement execute()")

    async def pre_execute(self, state: AgentState) -> AgentState:
        """Hook called before execute"""
        start_time = datetime.utcnow()
        state.metadata[f"{self.agent_type}_start_time"] = start_time.isoformat()

        self.logger.info(
            "agent_started",
            execution_id=state.execution_id,
            agent_name=self.name,
            agent_type=self.agent_type,
            company_id=state.company_id,
            start_time=start_time.isoformat()
        )
        return state

    async def post_execute(self, state: AgentState) -> AgentState:
        """Hook called after execute"""
        end_time = datetime.utcnow()
        state.metadata[f"{self.agent_type}_end_time"] = end_time.isoformat()

        # Calculate duration
        start_time_str = state.metadata.get(f"{self.agent_type}_start_time")
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str)
            duration = (end_time - start_time).total_seconds()
        else:
            duration = 0

        self.logger.info(
            "agent_completed",
            execution_id=state.execution_id,
            agent_name=self.name,
            agent_type=self.agent_type,
            company_id=state.company_id,
            duration_seconds=round(duration, 3),
            errors_count=len(state.errors),
            warnings_count=len(state.warnings),
            end_time=end_time.isoformat()
        )
        return state

    async def run(self, state: AgentState) -> AgentState:
        """Main entry point for agent execution"""
        try:
            state = await self.pre_execute(state)
            state = await self.execute(state)
            state = await self.post_execute(state)
        except Exception as e:
            self.logger.error(
                "agent_execution_failed",
                execution_id=state.execution_id,
                agent_name=self.name,
                agent_type=self.agent_type,
                company_id=state.company_id,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            state.errors.append(f"{self.agent_type}: {str(e)}")

        return state

    def log_action(self, action: str, details: Dict[str, Any] = None):
        """Log agent action"""
        self.logger.info(
            "agent_action",
            agent_name=self.name,
            agent_type=self.agent_type,
            action=action,
            **(details or {})
        )

    def log_warning(self, message: str, details: Dict[str, Any] = None):
        """Log agent warning"""
        self.logger.warning(
            "agent_warning",
            agent_name=self.name,
            agent_type=self.agent_type,
            message=message,
            **(details or {})
        )

    def log_error(self, message: str, error: Optional[Exception] = None, details: Dict[str, Any] = None):
        """Log agent error"""
        log_data = {
            "agent_name": self.name,
            "agent_type": self.agent_type,
            "message": message,
            **(details or {})
        }

        if error:
            log_data["error_type"] = type(error).__name__
            log_data["error_message"] = str(error)

        self.logger.error("agent_error", **log_data, exc_info=error is not None)
