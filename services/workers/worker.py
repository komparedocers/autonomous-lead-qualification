"""
Worker service for processing events and running AI agents
"""
import sys
import os
import asyncio
import json
from kafka import KafkaConsumer
from datetime import datetime
import structlog

# Add libs to path
sys.path.insert(0, "/libs")

from agents.discoverer import DiscovererAgent
from agents.enricher import EnricherAgent
from agents.scorer import ScorerAgent
from agents.proposer import ProposerAgent
from agents.base_agent import AgentState

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


class WorkerService:
    """Main worker service for processing events"""

    def __init__(self):
        self.kafka_brokers = os.getenv("KAFKA_BROKERS", "redpanda:9092").split(',')
        self.topics = [
            "raw.events",
            "clean.events",
            "signals.detected",
            "actions.triggered"
        ]

        # Initialize agents
        self.discoverer = DiscovererAgent()
        self.enricher = EnricherAgent()
        self.scorer = ScorerAgent()
        self.proposer = ProposerAgent()

        logger.info("Worker service initialized")

    def run(self):
        """Main worker loop"""
        logger.info("Starting worker service", topics=self.topics)

        consumer = KafkaConsumer(
            *self.topics,
            bootstrap_servers=self.kafka_brokers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='lead-qualification-workers',
            auto_offset_reset='latest',
            enable_auto_commit=True
        )

        logger.info("Connected to Kafka, consuming messages...")

        try:
            for message in consumer:
                asyncio.run(self.process_message(message))
        except KeyboardInterrupt:
            logger.info("Worker interrupted, shutting down...")
        finally:
            consumer.close()

    async def process_message(self, message):
        """Process a single Kafka message"""
        topic = message.topic
        data = message.value

        logger.info("Processing message", topic=topic, partition=message.partition, offset=message.offset)

        try:
            if topic == "raw.events":
                await self.process_raw_event(data)
            elif topic == "clean.events":
                await self.process_clean_event(data)
            elif topic == "signals.detected":
                await self.process_signal(data)
            elif topic == "actions.triggered":
                await self.process_action(data)
        except Exception as e:
            logger.error(f"Error processing message: {e}", topic=topic, exc_info=True)

    async def process_raw_event(self, data: dict):
        """Process raw event - clean and normalize"""
        logger.debug("Processing raw event", event_type=data.get("event_type"))

        # In production, this would:
        # 1. Clean and normalize text
        # 2. Extract entities (NER)
        # 3. Generate embeddings
        # 4. Publish to clean.events topic

        # Simplified for now
        pass

    async def process_clean_event(self, data: dict):
        """Process cleaned event - run analysis"""
        logger.debug("Processing clean event", event_type=data.get("event_type"))

        company_id = data.get("company_id")
        if not company_id:
            return

        # Run enrichment and scoring
        state = AgentState(
            company_id=company_id,
            company_data=data.get("company_data", {}),
            events=[data]
        )

        # Run enricher
        state = await self.enricher.run(state)

        # Run scorer
        state = await self.scorer.run(state)

        logger.info("Event processed", company_id=company_id, score=state.scores.get("overall"))

    async def process_signal(self, data: dict):
        """Process detected signal"""
        logger.info("Processing signal", signal_id=data.get("signal_id"), company_id=data.get("company_id"))

        # In production, this would:
        # 1. Determine actions based on signal score and type
        # 2. Trigger notifications
        # 3. Create CRM tasks
        # 4. Update KG

        signal_score = data.get("score", 0)

        if signal_score >= 80:
            logger.info("High-value signal detected, triggering actions", signal_id=data.get("signal_id"))
            # Would trigger proposal generation, CRM integration, etc.

    async def process_action(self, data: dict):
        """Process action trigger"""
        action_type = data.get("action_type")
        logger.info("Processing action", action_type=action_type)

        if action_type == "run_agent":
            await self.run_agent_playbook(data)
        elif action_type == "generate_proposal":
            await self.generate_proposal(data)
        elif action_type == "crm_sync":
            await self.sync_crm(data)

    async def run_agent_playbook(self, data: dict):
        """Run a specific agent playbook"""
        agent_type = data.get("agent_type")
        company_id = data.get("company_id")
        input_data = data.get("input_data", {})

        logger.info("Running agent playbook", agent_type=agent_type, company_id=company_id)

        # Initialize state
        state = AgentState(
            company_id=company_id,
            company_data=input_data.get("company_data", {}),
            events=input_data.get("events", []),
            signals=input_data.get("signals", [])
        )

        # Run appropriate agent
        if agent_type == "discoverer":
            state = await self.discoverer.run(state)
        elif agent_type == "enricher":
            state = await self.enricher.run(state)
        elif agent_type == "scorer":
            state = await self.scorer.run(state)
        elif agent_type == "proposer":
            state = await self.proposer.run(state)
        else:
            logger.warning(f"Unknown agent type: {agent_type}")
            return

        logger.info("Agent playbook completed", agent_type=agent_type, errors=len(state.errors))

        # Store results (would update database)

    async def generate_proposal(self, data: dict):
        """Generate proposal for company"""
        company_id = data.get("company_id")
        product_id = data.get("product_id")

        logger.info("Generating proposal", company_id=company_id, product_id=product_id)

        # In production, would:
        # 1. Fetch company data, signals, events
        # 2. Run proposer agent
        # 3. Generate PDF
        # 4. Store in MinIO
        # 5. Update database
        # 6. Send notifications

        # Simplified implementation
        state = AgentState(
            company_id=company_id,
            company_data=data.get("company_data", {}),
            signals=data.get("signals", []),
            events=data.get("events", [])
        )

        # Run scorer first to get scores
        state = await self.scorer.run(state)

        # Generate proposal
        state = await self.proposer.run(state)

        if state.proposal:
            logger.info("Proposal generated", company_id=company_id, length=len(state.proposal.get("content", "")))

    async def sync_crm(self, data: dict):
        """Sync with CRM system"""
        crm_type = data.get("crm_type")
        logger.info("CRM sync triggered", crm=crm_type)

        # In production, would integrate with Salesforce/HubSpot APIs
        # to push/pull data


if __name__ == "__main__":
    worker = WorkerService()
    worker.run()
