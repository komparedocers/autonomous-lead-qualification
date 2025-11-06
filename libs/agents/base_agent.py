"""
Base agent class for all AI agents
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import structlog

logger = structlog.get_logger()


@dataclass
class AgentState:
    """State container for agent execution"""
    company_id: Optional[int] = None
    company_data: Optional[Dict[str, Any]] = None
    signals: List[Dict[str, Any]] = None
    events: List[Dict[str, Any]] = None
    scores: Dict[str, float] = None
    proposal: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.signals is None:
            self.signals = []
        if self.events is None:
            self.events = []
        if self.scores is None:
            self.scores = {}
        if self.errors is None:
            self.errors = []
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
        self.logger.info("Agent starting", company_id=state.company_id)
        state.metadata[f"{self.agent_type}_start_time"] = datetime.utcnow().isoformat()
        return state

    async def post_execute(self, state: AgentState) -> AgentState:
        """Hook called after execute"""
        state.metadata[f"{self.agent_type}_end_time"] = datetime.utcnow().isoformat()
        self.logger.info("Agent completed", company_id=state.company_id)
        return state

    async def run(self, state: AgentState) -> AgentState:
        """Main entry point for agent execution"""
        try:
            state = await self.pre_execute(state)
            state = await self.execute(state)
            state = await self.post_execute(state)
        except Exception as e:
            self.logger.error(f"Agent execution failed: {e}", exc_info=True)
            state.errors.append(f"{self.agent_type}: {str(e)}")

        return state

    def log_action(self, action: str, details: Dict[str, Any] = None):
        """Log agent action"""
        self.logger.info(
            f"Agent action: {action}",
            agent=self.name,
            details=details or {}
        )
