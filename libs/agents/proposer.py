"""
Proposer Agent - generates tailored proposals using AI
"""
from typing import Dict, Any, List
import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from .base_agent import BaseAgent, AgentState


class ProposerAgent(BaseAgent):
    """
    Generates tailored proposals based on company context and signals
    - Retrieves company context from KG and events
    - Maps needs to product features
    - Generates proposal outline and content
    - Creates citations to evidence
    """

    def __init__(self):
        super().__init__(name="Proposer", agent_type="proposer")

        # Initialize LLM
        openai_key = os.getenv("OPENAI_API_KEY", "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

        if openai_key:
            self.llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.7)
        elif anthropic_key:
            self.llm = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0.7)
        else:
            self.llm = None
            self.logger.warning("No LLM API key configured, proposal generation unavailable")

    async def execute(self, state: AgentState) -> AgentState:
        """Execute proposal generation logic"""
        if not self.llm:
            state.errors.append("No LLM configured for proposal generation")
            return state

        if not state.company_data:
            state.errors.append("No company data for proposal")
            return state

        # Generate proposal
        proposal = await self.generate_proposal(
            company_data=state.company_data,
            signals=state.signals,
            events=state.events,
            scores=state.scores
        )

        state.proposal = proposal

        self.log_action("generated_proposal", {
            "company_id": state.company_id,
            "proposal_length": len(proposal.get("content", ""))
        })

        return state

    async def generate_proposal(
        self,
        company_data: Dict[str, Any],
        signals: List[Dict[str, Any]],
        events: List[Dict[str, Any]],
        scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate full proposal"""

        # Step 1: Create context summary
        context = self._build_context(company_data, signals, events, scores)

        # Step 2: Generate outline
        outline = await self._generate_outline(context)

        # Step 3: Generate full content
        content = await self._generate_content(context, outline)

        # Step 4: Extract evidence citations
        evidence = self._extract_evidence(signals, events)

        proposal = {
            "title": f"Proposal for {company_data.get('name', 'Your Company')}",
            "outline": outline,
            "content": content,
            "evidence": evidence,
            "context_summary": context
        }

        return proposal

    def _build_context(
        self,
        company_data: Dict[str, Any],
        signals: List[Dict[str, Any]],
        events: List[Dict[str, Any]],
        scores: Dict[str, float]
    ) -> str:
        """Build context summary for proposal generation"""
        context_parts = []

        # Company overview
        context_parts.append(f"Company: {company_data.get('name', 'N/A')}")
        context_parts.append(f"Industry: {company_data.get('industry', 'N/A')}")
        context_parts.append(f"Size: {company_data.get('employee_count', 'N/A')} employees")

        if company_data.get('description'):
            context_parts.append(f"Description: {company_data['description'][:300]}")

        # Tech stack
        tech_stack = company_data.get('tech_stack', [])
        if tech_stack:
            context_parts.append(f"Technologies: {', '.join(tech_stack[:10])}")

        # Key signals
        if signals:
            context_parts.append("\nKey Signals:")
            for signal in signals[:5]:
                context_parts.append(
                    f"- {signal.get('kind', 'N/A')}: {signal.get('explanation', 'N/A')[:100]}"
                )

        # Recent events
        if events:
            context_parts.append("\nRecent Activity:")
            for event in events[:3]:
                context_parts.append(
                    f"- {event.get('event_type', 'N/A')}: {event.get('title', 'N/A')}"
                )

        # Scores
        context_parts.append(f"\nLead Score: {scores.get('overall', 0)}/100")
        context_parts.append(f"- Fit: {scores.get('fit', 0)}")
        context_parts.append(f"- Intent: {scores.get('intent', 0)}")
        context_parts.append(f"- Timing: {scores.get('timing', 0)}")

        return "\n".join(context_parts)

    async def _generate_outline(self, context: str) -> str:
        """Generate proposal outline"""
        if not self.llm:
            return "Outline generation unavailable"

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a B2B sales proposal writer. Create a clear, compelling proposal outline based on the company context.

The outline should include:
1. Executive Summary
2. Understanding Your Challenges
3. Our Solution
4. Why Now
5. Implementation Approach
6. Expected Outcomes
7. Next Steps

Keep it concise and focused on the company's specific needs."""),
            ("user", f"""Company Context:
{context}

Generate a proposal outline:""")
        ])

        try:
            response = await self.llm.ainvoke(prompt.format_messages())
            return response.content
        except Exception as e:
            self.logger.error(f"Outline generation failed: {e}")
            return "Error generating outline"

    async def _generate_content(self, context: str, outline: str) -> str:
        """Generate full proposal content"""
        if not self.llm:
            return "Content generation unavailable"

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a B2B sales proposal writer. Write a compelling, data-driven proposal that addresses the company's specific needs.

Write in a professional but conversational tone. Use specific details from the context. Be concise but comprehensive.

Include specific evidence and references to the company's situation. Show that you understand their challenges and timing."""),
            ("user", f"""Company Context:
{context}

Outline:
{outline}

Write the full proposal content in Markdown format:""")
        ])

        try:
            response = await self.llm.ainvoke(prompt.format_messages())
            return response.content
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            return "Error generating content"

    def _extract_evidence(
        self,
        signals: List[Dict[str, Any]],
        events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract evidence citations"""
        evidence = []

        # Add signal evidence
        for signal in signals:
            signal_evidence = signal.get("evidence", [])
            if isinstance(signal_evidence, list):
                evidence.extend(signal_evidence)

        # Add event URLs
        for event in events[:10]:
            evidence.append({
                "url": event.get("url", ""),
                "title": event.get("title", ""),
                "timestamp": event.get("timestamp", ""),
                "type": event.get("event_type", "")
            })

        return evidence
