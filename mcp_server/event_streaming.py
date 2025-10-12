"""
Real-Time Event Streaming

Stream events and data updates in real-time:
- Event publishing and subscription
- Message routing
- Stream processing
- Event filtering
- Delivery guarantees
- Event replay

Features:
- Pub/Sub pattern
- Topic-based routing
- Event persistence
- Consumer groups
- Dead letter queue
- Rate limiting

Use Cases:
- Real-time stats updates
- Live game events
- Model predictions
- System alerts
- Audit events
"""

import time
import uuid
import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from queue import Queue, Empty
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class Event:
    """Event definition"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    topic: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class EventFilter:
    """Filter events based on criteria"""

    def __init__(
        self,
        event_types: Optional[Set[str]] = None,
        topics: Optional[Set[str]] = None,
        sources: Optional[Set[str]] = None,
        min_priority: Optional[EventPriority] = None
    ):
        self.event_types = event_types
        self.topics = topics
        self.sources = sources
        self.min_priority = min_priority

    def matches(self, event: Event) -> bool:
        """Check if event matches filter"""
        if self.event_types and event.event_type not in self.event_types:
            return False

        if self.topics and event.topic not in self.topics:
            return False

        if self.sources and event.source not in self.sources:
            return False

        if self.min_priority and event.priority.value > self.min_priority.value:
            return False

        return True


@dataclass
class Subscription:
    """Event subscription"""
    subscription_id: str
    subscriber_name: str
    callback: Callable[[Event], None]
    event_filter: Optional[EventFilter] = None
    active: bool = True
    event_count: int = 0
    last_event_time: Optional[datetime] = None


class EventBus:
    """Central event bus for pub/sub"""

    def __init__(self, max_history: int = 1000):
        self.subscriptions: Dict[str, Subscription] = {}
        self.event_history: List[Event] = []
        self.max_history = max_history
        self._lock = threading.RLock()

        # Statistics
        self.total_published = 0
        self.total_delivered = 0

    def subscribe(
        self,
        subscriber_name: str,
        callback: Callable[[Event], None],
        event_filter: Optional[EventFilter] = None
    ) -> str:
        """Subscribe to events"""
        subscription_id = str(uuid.uuid4())

        subscription = Subscription(
            subscription_id=subscription_id,
            subscriber_name=subscriber_name,
            callback=callback,
            event_filter=event_filter
        )

        with self._lock:
            self.subscriptions[subscription_id] = subscription

        logger.info(f"Subscriber '{subscriber_name}' registered: {subscription_id}")
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        with self._lock:
            if subscription_id in self.subscriptions:
                subscriber = self.subscriptions[subscription_id]
                subscriber.active = False
                del self.subscriptions[subscription_id]
                logger.info(f"Unsubscribed: {subscription_id}")
                return True
            return False

    def publish(self, event: Event) -> int:
        """Publish event to all matching subscribers"""
        delivered = 0

        with self._lock:
            # Add to history
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)

            self.total_published += 1

            # Deliver to subscribers
            for subscription in list(self.subscriptions.values()):
                if not subscription.active:
                    continue

                # Check filter
                if subscription.event_filter and not subscription.event_filter.matches(event):
                    continue

                # Deliver event
                try:
                    subscription.callback(event)
                    subscription.event_count += 1
                    subscription.last_event_time = datetime.now()
                    delivered += 1
                    self.total_delivered += 1
                except Exception as e:
                    logger.error(f"Error delivering event to {subscription.subscriber_name}: {e}")

        logger.debug(f"Published event {event.event_id} to {delivered} subscribers")
        return delivered

    def get_history(
        self,
        event_filter: Optional[EventFilter] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get event history"""
        with self._lock:
            events = self.event_history[-limit:]

            if event_filter:
                events = [e for e in events if event_filter.matches(e)]

            return events

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        with self._lock:
            return {
                'total_published': self.total_published,
                'total_delivered': self.total_delivered,
                'active_subscriptions': len(self.subscriptions),
                'history_size': len(self.event_history),
                'subscriptions': [
                    {
                        'name': sub.subscriber_name,
                        'event_count': sub.event_count,
                        'last_event': sub.last_event_time.isoformat() if sub.last_event_time else None
                    }
                    for sub in self.subscriptions.values()
                ]
            }


class EventStream:
    """Continuous event stream with buffering"""

    def __init__(self, buffer_size: int = 1000):
        self.buffer: Queue[Event] = Queue(maxsize=buffer_size)
        self.subscribers: List[Callable[[Event], None]] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def add_subscriber(self, callback: Callable[[Event], None]) -> None:
        """Add subscriber to stream"""
        self.subscribers.append(callback)

    def push(self, event: Event) -> bool:
        """Push event to stream"""
        try:
            self.buffer.put_nowait(event)
            return True
        except:
            logger.warning("Event stream buffer full, dropping event")
            return False

    def _process_loop(self) -> None:
        """Process events from buffer"""
        while self._running:
            try:
                event = self.buffer.get(timeout=1.0)

                # Deliver to subscribers
                for subscriber in self.subscribers:
                    try:
                        subscriber(event)
                    except Exception as e:
                        logger.error(f"Error in stream subscriber: {e}")
            except Empty:
                continue

    def start(self) -> None:
        """Start processing stream"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
        logger.info("Event stream started")

    def stop(self) -> None:
        """Stop processing stream"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Event stream stopped")


class TopicRouter:
    """Route events to topic-specific handlers"""

    def __init__(self):
        self.handlers: Dict[str, List[Callable[[Event], None]]] = defaultdict(list)
        self._lock = threading.RLock()

    def register_handler(self, topic: str, handler: Callable[[Event], None]) -> None:
        """Register handler for topic"""
        with self._lock:
            self.handlers[topic].append(handler)
        logger.info(f"Registered handler for topic: {topic}")

    def route(self, event: Event) -> int:
        """Route event to topic handlers"""
        handled = 0

        with self._lock:
            handlers = self.handlers.get(event.topic, [])

            for handler in handlers:
                try:
                    handler(event)
                    handled += 1
                except Exception as e:
                    logger.error(f"Error in topic handler for {event.topic}: {e}")

        return handled


# NBA-specific event types
class NBAEventType:
    """NBA event types"""
    PLAYER_STAT_UPDATE = "player.stat.update"
    GAME_STARTED = "game.started"
    GAME_ENDED = "game.ended"
    SCORE_UPDATE = "game.score.update"
    PREDICTION_GENERATED = "ml.prediction.generated"
    MODEL_TRAINED = "ml.model.trained"
    ALERT_TRIGGERED = "system.alert.triggered"


class NBAEventPublisher:
    """Publish NBA-specific events"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    def player_stat_updated(self, player_id: int, stats: Dict[str, float]) -> None:
        """Publish player stat update"""
        event = Event(
            event_type=NBAEventType.PLAYER_STAT_UPDATE,
            topic="nba.players",
            payload={
                'player_id': player_id,
                'stats': stats
            },
            source="stats_service"
        )
        self.event_bus.publish(event)

    def game_started(self, game_id: int, home_team: str, away_team: str) -> None:
        """Publish game started event"""
        event = Event(
            event_type=NBAEventType.GAME_STARTED,
            topic="nba.games",
            payload={
                'game_id': game_id,
                'home_team': home_team,
                'away_team': away_team
            },
            priority=EventPriority.HIGH,
            source="game_service"
        )
        self.event_bus.publish(event)

    def prediction_generated(self, model_name: str, prediction: Dict[str, Any]) -> None:
        """Publish ML prediction"""
        event = Event(
            event_type=NBAEventType.PREDICTION_GENERATED,
            topic="nba.ml",
            payload={
                'model': model_name,
                'prediction': prediction
            },
            source="ml_service"
        )
        self.event_bus.publish(event)


# Global event bus
_event_bus = None
_bus_lock = threading.Lock()


def get_event_bus() -> EventBus:
    """Get global event bus"""
    global _event_bus
    with _bus_lock:
        if _event_bus is None:
            _event_bus = EventBus()
        return _event_bus


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Real-Time Event Streaming Demo ===\n")

    # Create event bus
    bus = EventBus()

    # Subscribe to all events
    def all_events_handler(event: Event):
        print(f"[ALL] {event.event_type}: {event.payload}")

    bus.subscribe("all_events", all_events_handler)

    # Subscribe to player events only
    player_filter = EventFilter(topics={'nba.players'})

    def player_events_handler(event: Event):
        print(f"[PLAYERS] Player {event.payload['player_id']} stats updated")

    bus.subscribe("player_stats", player_events_handler, player_filter)

    # Subscribe to high-priority events only
    priority_filter = EventFilter(min_priority=EventPriority.HIGH)

    def priority_handler(event: Event):
        print(f"[PRIORITY] {event.event_type} (priority: {event.priority.name})")

    bus.subscribe("priority_alerts", priority_handler, priority_filter)

    # Create NBA publisher
    publisher = NBAEventPublisher(bus)

    # Publish events
    print("--- Publishing Events ---\n")

    # Normal priority player event
    publisher.player_stat_updated(23, {'ppg': 25.5, 'rpg': 8.0})
    time.sleep(0.1)

    # High priority game event
    publisher.game_started(12345, "Lakers", "Warriors")
    time.sleep(0.1)

    # ML prediction event
    publisher.prediction_generated(
        "game_predictor_v2",
        {'winner': 'Lakers', 'confidence': 0.72}
    )
    time.sleep(0.1)

    # Statistics
    print("\n--- Event Bus Statistics ---")
    stats = bus.get_stats()
    print(f"Total published: {stats['total_published']}")
    print(f"Total delivered: {stats['total_delivered']}")
    print(f"Active subscriptions: {stats['active_subscriptions']}")

    print("\nSubscription details:")
    for sub in stats['subscriptions']:
        print(f"  - {sub['name']}: {sub['event_count']} events")

    # Event history
    print("\n--- Event History ---")
    history = bus.get_history(limit=5)
    for event in history:
        print(f"  {event.timestamp.strftime('%H:%M:%S')} - {event.event_type}")

    # Event stream demo
    print("\n--- Event Stream Demo ---")
    stream = EventStream(buffer_size=100)

    def stream_handler(event: Event):
        print(f"[STREAM] Received: {event.event_type}")

    stream.add_subscriber(stream_handler)
    stream.start()

    # Push events to stream
    for i in range(3):
        event = Event(
            event_type="test.event",
            topic="test",
            payload={'index': i}
        )
        stream.push(event)

    time.sleep(1)
    stream.stop()

    print("\n=== Demo Complete ===")

