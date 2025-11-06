"""
Enricher Agent - enriches company data with additional context
"""
from typing import Dict, Any, List, Optional
import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from .base_agent import BaseAgent, AgentState


class EnricherAgent(BaseAgent):
    """
    Enriches company data with additional context
    - Fills in missing firmographics
    - Identifies technographics
    - Extracts intent features from events
    - Categorizes companies by segment
    """

    def __init__(self):
        super().__init__(name="Enricher", agent_type="enricher")

        # Initialize LLM
        openai_key = os.getenv("OPENAI_API_KEY", "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

        if openai_key:
            self.llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
        elif anthropic_key:
            self.llm = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0)
        else:
            self.llm = None
            self.logger.warning("No LLM API key configured, enrichment will be limited")

    async def execute(self, state: AgentState) -> AgentState:
        """Execute enrichment logic"""
        if not state.company_data:
            state.errors.append("No company data to enrich")
            return state

        # Enrich firmographics
        if self.llm and state.events:
            enriched_data = await self.enrich_from_events(
                state.company_data,
                state.events
            )
            state.company_data.update(enriched_data)

        # Extract tech stack
        tech_stack = await self.extract_tech_stack(state.events)
        state.company_data["tech_stack"] = tech_stack

        # Categorize company
        category = await self.categorize_company(state.company_data)
        state.company_data["category"] = category

        self.log_action("enriched_company", {
            "company_id": state.company_id,
            "tech_count": len(tech_stack)
        })

        return state

    async def enrich_from_events(
        self,
        company_data: Dict[str, Any],
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use LLM to extract additional company info from events"""
        if not self.llm or not events:
            return {}

        # Prepare events text
        events_text = "\n\n".join([
            f"Event: {e.get('title', 'N/A')}\n{e.get('text', '')[:500]}"
            for e in events[:10]  # Use first 10 events
        ])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a company intelligence analyst. Extract and infer company information from the provided events.

Extract:
- Industry and sector
- Company size indicators
- Key products or services
- Target market
- Company stage (startup, growth, enterprise)
- Any funding or growth signals

Return as JSON with keys: industry, sector, size_estimate, products, target_market, stage, growth_signals"""),
            ("user", f"""Company: {company_data.get('name', 'Unknown')}
Domain: {company_data.get('domain', 'Unknown')}

Recent Events:
{events_text}

Extract company information as JSON:""")
        ])

        try:
            response = await self.llm.ainvoke(prompt.format_messages())
            # Parse JSON response
            import json
            enriched = json.loads(response.content)
            return enriched
        except Exception as e:
            self.logger.error(f"LLM enrichment failed: {e}")
            return {}

    async def extract_tech_stack(self, events: List[Dict[str, Any]]) -> List[str]:
        """Extract technology stack from events"""
        tech_keywords = {
            # Cloud & Infrastructure
            "aws", "azure", "gcp", "google cloud", "kubernetes", "docker",
            # Databases
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb",
            # Programming
            "python", "java", "javascript", "typescript", "go", "rust", "node.js",
            # Frameworks
            "react", "angular", "vue", "django", "flask", "spring", "express",
            # Data & ML
            "spark", "hadoop", "tensorflow", "pytorch", "airflow", "kafka",
            # Analytics
            "snowflake", "databricks", "tableau", "looker", "power bi",
            # CRM & Sales
            "salesforce", "hubspot", "pipedrive",
            # Other
            "github", "gitlab", "jenkins", "terraform", "ansible"
        }

        found_tech = set()

        for event in events:
            text = (event.get("text", "") + " " + event.get("title", "")).lower()
            for tech in tech_keywords:
                if tech in text:
                    found_tech.add(tech.title())

        return list(found_tech)

    async def categorize_company(self, company_data: Dict[str, Any]) -> str:
        """Categorize company into segments"""
        # Simple rule-based categorization
        # In production, would use ML classifier

        employee_count = company_data.get("employee_count", 0)

        if employee_count < 50:
            return "small_business"
        elif employee_count < 500:
            return "mid_market"
        else:
            return "enterprise"

    async def identify_pain_points(
        self,
        events: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify potential pain points from events"""
        pain_indicators = [
            "looking for", "need help", "challenge", "problem",
            "struggling", "difficulty", "improve", "better solution"
        ]

        pain_points = []

        for event in events:
            text = (event.get("text", "") + " " + event.get("title", "")).lower()
            for indicator in pain_indicators:
                if indicator in text:
                    # Extract context around pain indicator
                    idx = text.find(indicator)
                    context = text[max(0, idx-50):idx+100]
                    pain_points.append(context.strip())

        return pain_points[:5]  # Return top 5
