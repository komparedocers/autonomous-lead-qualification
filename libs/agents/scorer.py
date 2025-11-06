"""
Scorer Agent - scores leads based on fit, intent, and timing
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from .base_agent import BaseAgent, AgentState


class ScorerAgent(BaseAgent):
    """
    Scores leads using FIT + INTENT + TIMING model
    - FIT: How well company matches ICP (firmographics + technographics)
    - INTENT: Buying signals from events (hiring, tech changes, etc.)
    - TIMING: Velocity and recency of signals
    """

    def __init__(self):
        super().__init__(name="Scorer", agent_type="scorer")

        # Scoring weights (from architecture)
        self.fit_weight = 0.4
        self.intent_weight = 0.4
        self.timing_weight = 0.2

    async def execute(self, state: AgentState) -> AgentState:
        """Execute scoring logic"""
        if not state.company_data:
            state.errors.append("No company data to score")
            return state

        # Calculate component scores
        fit_score = await self.calculate_fit_score(state.company_data)
        intent_score = await self.calculate_intent_score(state.events, state.signals)
        timing_score = await self.calculate_timing_score(state.events, state.signals)

        # Calculate overall score
        overall_score = (
            fit_score * self.fit_weight +
            intent_score * self.intent_weight +
            timing_score * self.timing_weight
        )

        # Store scores
        state.scores = {
            "overall": round(overall_score, 2),
            "fit": round(fit_score, 2),
            "intent": round(intent_score, 2),
            "timing": round(timing_score, 2)
        }

        # Evaluate qualification frameworks
        state.scores["bant_qualified"] = await self.check_bant_qualification(state)
        state.scores["champ_qualified"] = await self.check_champ_qualification(state)

        self.log_action("scored_lead", {
            "company_id": state.company_id,
            "score": overall_score
        })

        return state

    async def calculate_fit_score(self, company_data: Dict[str, Any]) -> float:
        """
        Calculate ICP fit score based on firmographics and technographics
        100 = perfect fit, 0 = poor fit
        """
        score = 0.0

        # Industry fit (30 points)
        target_industries = ["technology", "fintech", "saas", "healthcare", "enterprise"]
        industry = company_data.get("industry", "").lower()
        if any(target in industry for target in target_industries):
            score += 30

        # Size fit (30 points)
        employee_count = company_data.get("employee_count", 0)
        if 200 <= employee_count <= 5000:  # Sweet spot
            score += 30
        elif 50 <= employee_count < 200 or 5000 < employee_count <= 10000:
            score += 20
        elif employee_count > 0:
            score += 10

        # Tech stack fit (20 points)
        tech_stack = company_data.get("tech_stack", [])
        modern_tech_count = sum(
            1 for tech in tech_stack
            if any(modern in tech.lower() for modern in [
                "aws", "azure", "gcp", "kubernetes", "python", "react",
                "microservices", "api"
            ])
        )
        score += min(modern_tech_count * 5, 20)

        # Funding/Revenue fit (20 points)
        if company_data.get("total_funding", 0) > 0:
            score += 10
        if company_data.get("revenue"):
            score += 10

        return min(score, 100)

    async def calculate_intent_score(
        self,
        events: List[Dict[str, Any]],
        signals: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate intent score based on buying signals
        100 = high intent, 0 = no intent
        """
        score = 0.0

        # Recent hiring signals (30 points)
        recent_events = [
            e for e in events
            if self._is_recent(e.get("timestamp"), days=30)
        ]

        hiring_events = [
            e for e in recent_events
            if e.get("event_type") in ["job_posting", "careers"]
        ]
        score += min(len(hiring_events) * 5, 30)

        # Tech adoption signals (25 points)
        tech_change_signals = [
            s for s in signals
            if s.get("kind") == "tech_adoption"
        ]
        score += min(len(tech_change_signals) * 12.5, 25)

        # Funding events (20 points)
        funding_signals = [
            s for s in signals
            if s.get("kind") in ["funding_event", "budget_event"]
        ]
        if funding_signals:
            score += 20

        # Expansion signals (15 points)
        expansion_signals = [
            s for s in signals
            if s.get("kind") in ["expansion", "product_launch"]
        ]
        score += min(len(expansion_signals) * 7.5, 15)

        # Pain point mentions (10 points)
        pain_point_signals = [
            s for s in signals
            if s.get("kind") == "pain_point"
        ]
        score += min(len(pain_point_signals) * 5, 10)

        return min(score, 100)

    async def calculate_timing_score(
        self,
        events: List[Dict[str, Any]],
        signals: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate timing score based on recency and velocity
        100 = perfect timing, 0 = poor timing
        """
        score = 0.0

        now = datetime.utcnow()

        # Recency score (50 points)
        # More recent activity = higher score
        recent_7d = [e for e in events if self._is_recent(e.get("timestamp"), days=7)]
        recent_30d = [e for e in events if self._is_recent(e.get("timestamp"), days=30)]
        recent_90d = [e for e in events if self._is_recent(e.get("timestamp"), days=90)]

        if recent_7d:
            score += 50
        elif recent_30d:
            score += 35
        elif recent_90d:
            score += 20

        # Velocity score (50 points)
        # Increasing activity = higher score
        if len(recent_30d) > len(recent_90d) - len(recent_30d):
            score += 50  # Accelerating
        elif len(recent_30d) > 0:
            score += 25  # Steady

        return min(score, 100)

    async def check_bant_qualification(self, state: AgentState) -> bool:
        """
        Check BANT (Budget, Authority, Need, Timeline) qualification
        """
        company_data = state.company_data
        signals = state.signals

        # Budget: Has funding or revenue
        has_budget = (
            company_data.get("total_funding", 0) > 0 or
            company_data.get("revenue") is not None
        )

        # Authority: Company size suggests decision makers accessible
        has_authority = company_data.get("employee_count", 0) < 5000

        # Need: Has relevant signals
        has_need = len(signals) > 0

        # Timeline: Recent activity
        has_timeline = any(
            self._is_recent(s.get("timestamp_start"), days=90)
            for s in signals
        )

        return all([has_budget, has_authority, has_need, has_timeline])

    async def check_champ_qualification(self, state: AgentState) -> bool:
        """
        Check CHAMP (Challenges, Authority, Money, Prioritization) qualification
        """
        signals = state.signals

        # Challenges: Has pain points or hiring signals
        has_challenges = any(
            s.get("kind") in ["pain_point", "hiring_spike"]
            for s in signals
        )

        # Authority: Similar to BANT
        has_authority = state.company_data.get("employee_count", 0) < 5000

        # Money: Has funding
        has_money = state.company_data.get("total_funding", 0) > 0

        # Prioritization: Recent high-score signals
        has_priority = any(
            s.get("score", 0) > 75 and self._is_recent(s.get("timestamp_start"), days=30)
            for s in signals
        )

        return all([has_challenges, has_authority, has_money, has_priority])

    def _is_recent(self, timestamp, days: int = 30) -> bool:
        """Check if timestamp is within last N days"""
        if not timestamp:
            return False

        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        cutoff = datetime.utcnow() - timedelta(days=days)
        return timestamp > cutoff
