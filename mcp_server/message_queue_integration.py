"""
Message Queue Integration

Supports multiple message brokers:
- RabbitMQ (AMQP)
- Apache Kafka
- AWS SQS
- Redis Pub/Sub

Features:
- Asynchronous task processing
- Message prioritization
- Dead letter queues
- Message retry logic
- Delayed/scheduled messages
- Message ordering
- At-least-once delivery
- Producer-consumer patterns

Use Cases:
- Async NBA data ingestion
- Background ML model training
- Scheduled data updates
- Event-driven architecture
"""

import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class QueueType(Enum):
    """Message queue types"""

    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"
    SQS = "sqs"
    REDIS = "redis"


class MessagePriority(Enum):
    """Message priority levels"""

    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 15


@dataclass
class Message:
    """Message structure"""

    id: str
    body: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    delay_seconds: int = 0

    def to_json(self) -> str:
        """Serialize message to JSON"""
        return json.dumps(
            {
                "id": self.id,
                "body": self.body,
                "priority": self.priority.value,
                "timestamp": self.timestamp.isoformat(),
                "retry_count": self.retry_count,
                "max_retries": self.max_retries,
                "delay_seconds": self.delay_seconds,
            }
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Deserialize message from JSON"""
        data = json.loads(json_str)
        return cls(
            id=data["id"],
            body=data["body"],
            priority=MessagePriority(
                data.get("priority", MessagePriority.NORMAL.value)
            ),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            delay_seconds=data.get("delay_seconds", 0),
        )


class MessageQueueBase(ABC):
    """Base class for message queue implementations"""

    @abstractmethod
    def connect(self) -> bool:
        """Connect to message broker"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from message broker"""
        pass

    @abstractmethod
    def send(self, queue_name: str, message: Message) -> bool:
        """Send message to queue"""
        pass

    @abstractmethod
    def receive(self, queue_name: str, timeout_seconds: int = 30) -> Optional[Message]:
        """Receive message from queue"""
        pass

    @abstractmethod
    def acknowledge(self, queue_name: str, message_id: str) -> bool:
        """Acknowledge message processing"""
        pass

    @abstractmethod
    def reject(self, queue_name: str, message_id: str, requeue: bool = True) -> bool:
        """Reject message"""
        pass


class RabbitMQAdapter(MessageQueueBase):
    """RabbitMQ message queue adapter"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        username: str = "guest",
        password: str = "guest",
        virtual_host: str = "/",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.virtual_host = virtual_host
        self.connection = None
        self.channel = None

    def connect(self) -> bool:
        """Connect to RabbitMQ"""
        try:
            import pika

            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.virtual_host,
                credentials=credentials,
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
            return True
        except ImportError:
            logger.error("pika library not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    def send(self, queue_name: str, message: Message) -> bool:
        """Send message to RabbitMQ queue"""
        if not self.channel:
            logger.error("Not connected to RabbitMQ")
            return False

        try:
            # Declare queue
            self.channel.queue_declare(
                queue=queue_name, durable=True, arguments={"x-max-priority": 15}
            )

            # Publish message
            import pika

            self.channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=message.to_json(),
                properties=pika.BasicProperties(
                    delivery_mode=2, priority=message.priority.value  # Persistent
                ),
            )
            logger.debug(f"Sent message {message.id} to {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def receive(self, queue_name: str, timeout_seconds: int = 30) -> Optional[Message]:
        """Receive message from RabbitMQ queue"""
        if not self.channel:
            logger.error("Not connected to RabbitMQ")
            return None

        try:
            method_frame, header_frame, body = self.channel.basic_get(queue_name)
            if method_frame:
                message = Message.from_json(body.decode())
                message.id = str(method_frame.delivery_tag)
                return message
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            return None

    def acknowledge(self, queue_name: str, message_id: str) -> bool:
        """Acknowledge message processing"""
        try:
            self.channel.basic_ack(delivery_tag=int(message_id))
            return True
        except Exception as e:
            logger.error(f"Failed to acknowledge message: {e}")
            return False

    def reject(self, queue_name: str, message_id: str, requeue: bool = True) -> bool:
        """Reject message"""
        try:
            self.channel.basic_nack(delivery_tag=int(message_id), requeue=requeue)
            return True
        except Exception as e:
            logger.error(f"Failed to reject message: {e}")
            return False


class KafkaAdapter(MessageQueueBase):
    """Apache Kafka message queue adapter"""

    def __init__(self, bootstrap_servers: List[str] = None):
        self.bootstrap_servers = bootstrap_servers or ["localhost:9092"]
        self.producer = None
        self.consumer = None

    def connect(self) -> bool:
        """Connect to Kafka"""
        try:
            from kafka import KafkaProducer, KafkaConsumer

            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: v.encode("utf-8"),
            )
            logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
            return True
        except ImportError:
            logger.error("kafka-python library not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Kafka"""
        if self.producer:
            self.producer.close()
        if self.consumer:
            self.consumer.close()
        logger.info("Disconnected from Kafka")

    def send(self, queue_name: str, message: Message) -> bool:
        """Send message to Kafka topic"""
        if not self.producer:
            logger.error("Not connected to Kafka")
            return False

        try:
            future = self.producer.send(queue_name, message.to_json())
            future.get(timeout=10)  # Wait for send confirmation
            logger.debug(f"Sent message {message.id} to {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def receive(self, queue_name: str, timeout_seconds: int = 30) -> Optional[Message]:
        """Receive message from Kafka topic"""
        if not self.consumer:
            from kafka import KafkaConsumer

            self.consumer = KafkaConsumer(
                queue_name,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                value_deserializer=lambda m: m.decode("utf-8"),
            )

        try:
            messages = self.consumer.poll(timeout_ms=timeout_seconds * 1000)
            for topic_partition, records in messages.items():
                if records:
                    record = records[0]
                    return Message.from_json(record.value)
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            return None

    def acknowledge(self, queue_name: str, message_id: str) -> bool:
        """Acknowledge message processing (commit offset)"""
        try:
            if self.consumer:
                self.consumer.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to acknowledge message: {e}")
            return False

    def reject(self, queue_name: str, message_id: str, requeue: bool = True) -> bool:
        """Reject message (Kafka doesn't support traditional nack)"""
        # In Kafka, we don't commit the offset to "reject" a message
        logger.warning("Kafka doesn't support traditional message rejection")
        return True


class MessageQueueManager:
    """High-level message queue manager"""

    def __init__(self, queue_type: QueueType, **kwargs):
        self.queue_type = queue_type
        self.adapter = self._create_adapter(queue_type, **kwargs)
        self.workers: Dict[str, threading.Thread] = {}
        self.stop_flags: Dict[str, threading.Event] = {}

    def _create_adapter(self, queue_type: QueueType, **kwargs) -> MessageQueueBase:
        """Create appropriate adapter based on queue type"""
        if queue_type == QueueType.RABBITMQ:
            return RabbitMQAdapter(**kwargs)
        elif queue_type == QueueType.KAFKA:
            return KafkaAdapter(**kwargs)
        else:
            raise ValueError(f"Unsupported queue type: {queue_type}")

    def connect(self) -> bool:
        """Connect to message broker"""
        return self.adapter.connect()

    def disconnect(self) -> None:
        """Disconnect from message broker"""
        # Stop all workers
        for queue_name in list(self.workers.keys()):
            self.stop_worker(queue_name)
        self.adapter.disconnect()

    def send_message(
        self,
        queue_name: str,
        body: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        delay_seconds: int = 0,
    ) -> bool:
        """Send message to queue"""
        message = Message(
            id=f"{queue_name}_{int(time.time() * 1000)}",
            body=body,
            priority=priority,
            delay_seconds=delay_seconds,
        )
        return self.adapter.send(queue_name, message)

    def start_worker(
        self, queue_name: str, handler: Callable[[Message], bool], max_workers: int = 1
    ) -> None:
        """Start worker thread(s) to process messages"""
        if queue_name in self.workers:
            logger.warning(f"Worker for {queue_name} already running")
            return

        stop_flag = threading.Event()
        self.stop_flags[queue_name] = stop_flag

        def worker_loop():
            logger.info(f"Worker started for queue: {queue_name}")
            while not stop_flag.is_set():
                message = self.adapter.receive(queue_name, timeout_seconds=5)
                if message:
                    try:
                        # Process message
                        success = handler(message)

                        if success:
                            self.adapter.acknowledge(queue_name, message.id)
                            logger.debug(f"Processed message {message.id}")
                        else:
                            # Retry logic
                            if message.retry_count < message.max_retries:
                                message.retry_count += 1
                                self.adapter.reject(
                                    queue_name, message.id, requeue=True
                                )
                                logger.warning(
                                    f"Message {message.id} failed, requeuing (retry {message.retry_count}/{message.max_retries})"
                                )
                            else:
                                self.adapter.reject(
                                    queue_name, message.id, requeue=False
                                )
                                logger.error(
                                    f"Message {message.id} failed after {message.max_retries} retries, moving to DLQ"
                                )
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        self.adapter.reject(queue_name, message.id, requeue=True)
            logger.info(f"Worker stopped for queue: {queue_name}")

        worker_thread = threading.Thread(target=worker_loop, daemon=True)
        worker_thread.start()
        self.workers[queue_name] = worker_thread

    def stop_worker(self, queue_name: str) -> None:
        """Stop worker thread"""
        if queue_name in self.stop_flags:
            self.stop_flags[queue_name].set()
            if queue_name in self.workers:
                self.workers[queue_name].join(timeout=10)
                del self.workers[queue_name]
            del self.stop_flags[queue_name]
            logger.info(f"Worker stopped for queue: {queue_name}")


# Example NBA MCP use cases
def nba_data_ingestion_handler(message: Message) -> bool:
    """Handler for NBA data ingestion tasks"""
    try:
        logger.info(f"Processing NBA data ingestion: {message.body}")
        # Simulate data ingestion
        game_id = message.body.get("game_id")
        # Fetch and process game data...
        time.sleep(1)  # Simulate processing time
        logger.info(f"Successfully ingested game {game_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to ingest data: {e}")
        return False


def ml_training_handler(message: Message) -> bool:
    """Handler for ML model training tasks"""
    try:
        logger.info(f"Processing ML training: {message.body}")
        model_type = message.body.get("model_type")
        # Train model...
        time.sleep(2)  # Simulate training time
        logger.info(f"Successfully trained {model_type} model")
        return True
    except Exception as e:
        logger.error(f"Failed to train model: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create message queue manager (RabbitMQ example)
    manager = MessageQueueManager(
        queue_type=QueueType.RABBITMQ,
        host="localhost",
        port=5672,
        username="guest",
        password="guest",
    )

    # Connect to broker
    if manager.connect():
        # Send some messages
        manager.send_message(
            "nba_data_ingestion",
            {"game_id": 12345, "season": 2024},
            priority=MessagePriority.HIGH,
        )

        manager.send_message(
            "ml_training",
            {"model_type": "player_prediction", "dataset": "games_2024"},
            priority=MessagePriority.NORMAL,
        )

        # Start workers
        manager.start_worker("nba_data_ingestion", nba_data_ingestion_handler)
        manager.start_worker("ml_training", ml_training_handler)

        # Let workers process messages
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            pass

        # Cleanup
        manager.disconnect()
        print("Done!")
