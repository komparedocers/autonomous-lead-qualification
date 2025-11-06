"""
Kafka/Redpanda service for streaming events
"""
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import json
import structlog
from config import settings

logger = structlog.get_logger()


class KafkaService:
    """Kafka service wrapper"""

    def __init__(self):
        self.producer = None
        self.brokers = settings.KAFKA_BROKERS.split(',')
        self.topics = settings.KAFKA_TOPICS

    async def start(self):
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.brokers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                compression_type='gzip'
            )
            logger.info("Kafka producer initialized", brokers=self.brokers)

            # Create topics if they don't exist
            await self._ensure_topics()

        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise

    async def stop(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer closed")

    async def _ensure_topics(self):
        """Ensure all required topics exist"""
        # Topics are auto-created in Redpanda with default config
        pass

    async def publish(self, topic: str, message: dict, key: str = None):
        """Publish message to Kafka topic"""
        try:
            future = self.producer.send(topic, value=message, key=key)
            metadata = future.get(timeout=10)
            logger.debug(
                "Message published",
                topic=topic,
                partition=metadata.partition,
                offset=metadata.offset
            )
            return True
        except KafkaError as e:
            logger.error(f"Failed to publish message: {e}", topic=topic)
            return False

    async def publish_event(self, event_type: str, data: dict):
        """Publish event to raw.events topic"""
        message = {
            "event_type": event_type,
            "data": data,
            "timestamp": data.get("timestamp")
        }
        return await self.publish(self.topics["raw_events"], message)

    async def publish_signal(self, signal_data: dict):
        """Publish detected signal"""
        return await self.publish(
            self.topics["signals_detected"],
            signal_data,
            key=str(signal_data.get("company_id"))
        )

    async def publish_action(self, action_data: dict):
        """Publish action trigger"""
        return await self.publish(
            self.topics["actions_triggered"],
            action_data,
            key=str(action_data.get("signal_id"))
        )


# Global instance
kafka_producer = KafkaService()
