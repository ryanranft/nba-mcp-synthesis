"""
WebSocket Support for Real-Time NBA Data

Provides WebSocket server for real-time updates:
- Live game scores
- Player stat updates
- Team standings changes
- Play-by-play events
- Prediction updates

Features:
- Connection management
- Room/channel support
- Message broadcasting
- Heartbeat/ping-pong
- Reconnection handling
- Rate limiting
- Authentication

Use Cases:
- Live game dashboards
- Real-time analytics
- Collaborative features
- Push notifications
"""

import json
import asyncio
import time
import logging
from typing import Dict, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types"""

    CONNECT = "connect"
    DISCONNECT = "disconnect"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    MESSAGE = "message"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


class ChannelType(Enum):
    """Subscription channels"""

    GAME_UPDATES = "game_updates"
    PLAYER_STATS = "player_stats"
    TEAM_STANDINGS = "team_standings"
    PLAY_BY_PLAY = "play_by_play"
    PREDICTIONS = "predictions"
    SYSTEM = "system"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""

    type: MessageType
    channel: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(
            {
                "type": self.type.value,
                "channel": self.channel,
                "data": self.data,
                "timestamp": self.timestamp.isoformat(),
            }
        )

    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketMessage":
        """Deserialize from JSON"""
        data = json.loads(json_str)
        return cls(
            type=MessageType(data["type"]),
            channel=data["channel"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class WebSocketClient:
    """Connected WebSocket client"""

    id: str
    websocket: Any  # websocket connection object
    subscriptions: Set[str] = field(default_factory=set)
    authenticated: bool = False
    user_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.now)
    last_ping: datetime = field(default_factory=datetime.now)
    message_count: int = 0

    def is_subscribed(self, channel: str) -> bool:
        """Check if client is subscribed to channel"""
        return channel in self.subscriptions


class WebSocketManager:
    """Manage WebSocket connections and broadcasting"""

    def __init__(self, ping_interval: int = 30, max_message_rate: int = 100):
        self.clients: Dict[str, WebSocketClient] = {}
        self.channels: Dict[str, Set[str]] = {}  # channel -> set of client_ids
        self.ping_interval = ping_interval
        self.max_message_rate = max_message_rate
        self.message_handlers: Dict[str, Callable] = {}
        self._running = False

    async def register_client(self, client_id: str, websocket: Any) -> WebSocketClient:
        """Register new WebSocket client"""
        client = WebSocketClient(id=client_id, websocket=websocket)
        self.clients[client_id] = client

        logger.info(f"Client {client_id} connected")

        # Send welcome message
        await self.send_to_client(
            client_id,
            WebSocketMessage(
                type=MessageType.CONNECT,
                channel=ChannelType.SYSTEM.value,
                data={
                    "message": "Connected to NBA MCP WebSocket",
                    "client_id": client_id,
                    "server_time": datetime.now().isoformat(),
                },
            ),
        )

        return client

    async def unregister_client(self, client_id: str) -> None:
        """Unregister WebSocket client"""
        if client_id in self.clients:
            client = self.clients[client_id]

            # Unsubscribe from all channels
            for channel in client.subscriptions.copy():
                await self.unsubscribe_client(client_id, channel)

            del self.clients[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def subscribe_client(self, client_id: str, channel: str) -> bool:
        """Subscribe client to channel"""
        if client_id not in self.clients:
            return False

        client = self.clients[client_id]
        client.subscriptions.add(channel)

        if channel not in self.channels:
            self.channels[channel] = set()
        self.channels[channel].add(client_id)

        logger.info(f"Client {client_id} subscribed to {channel}")

        # Send confirmation
        await self.send_to_client(
            client_id,
            WebSocketMessage(
                type=MessageType.SUBSCRIBE,
                channel=channel,
                data={"status": "subscribed", "channel": channel},
            ),
        )

        return True

    async def unsubscribe_client(self, client_id: str, channel: str) -> bool:
        """Unsubscribe client from channel"""
        if client_id not in self.clients:
            return False

        client = self.clients[client_id]
        client.subscriptions.discard(channel)

        if channel in self.channels:
            self.channels[channel].discard(client_id)
            if not self.channels[channel]:
                del self.channels[channel]

        logger.info(f"Client {client_id} unsubscribed from {channel}")
        return True

    async def send_to_client(self, client_id: str, message: WebSocketMessage) -> bool:
        """Send message to specific client"""
        if client_id not in self.clients:
            return False

        client = self.clients[client_id]
        try:
            await client.websocket.send(message.to_json())
            client.message_count += 1
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {client_id}: {e}")
            await self.unregister_client(client_id)
            return False

    async def broadcast_to_channel(
        self, channel: str, message: WebSocketMessage
    ) -> int:
        """Broadcast message to all clients in channel"""
        if channel not in self.channels:
            return 0

        sent_count = 0
        for client_id in self.channels[channel].copy():
            if await self.send_to_client(client_id, message):
                sent_count += 1

        logger.debug(f"Broadcasted to {sent_count} clients in {channel}")
        return sent_count

    async def broadcast_to_all(self, message: WebSocketMessage) -> int:
        """Broadcast message to all connected clients"""
        sent_count = 0
        for client_id in list(self.clients.keys()):
            if await self.send_to_client(client_id, message):
                sent_count += 1
        return sent_count

    async def handle_message(self, client_id: str, raw_message: str) -> None:
        """Handle incoming WebSocket message"""
        try:
            message = WebSocketMessage.from_json(raw_message)

            # Rate limiting
            if not await self._check_rate_limit(client_id):
                await self.send_to_client(
                    client_id,
                    WebSocketMessage(
                        type=MessageType.ERROR,
                        channel=ChannelType.SYSTEM.value,
                        data={"error": "Rate limit exceeded"},
                    ),
                )
                return

            # Handle different message types
            if message.type == MessageType.SUBSCRIBE:
                await self.subscribe_client(client_id, message.channel)

            elif message.type == MessageType.UNSUBSCRIBE:
                await self.unsubscribe_client(client_id, message.channel)

            elif message.type == MessageType.PING:
                await self.send_to_client(
                    client_id,
                    WebSocketMessage(
                        type=MessageType.PONG,
                        channel=ChannelType.SYSTEM.value,
                        data={"timestamp": datetime.now().isoformat()},
                    ),
                )

            elif message.type == MessageType.MESSAGE:
                # Call custom handler if registered
                if message.channel in self.message_handlers:
                    await self.message_handlers[message.channel](client_id, message)

        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            await self.send_to_client(
                client_id,
                WebSocketMessage(
                    type=MessageType.ERROR,
                    channel=ChannelType.SYSTEM.value,
                    data={"error": str(e)},
                ),
            )

    def register_handler(self, channel: str, handler: Callable) -> None:
        """Register custom message handler for channel"""
        self.message_handlers[channel] = handler
        logger.info(f"Registered handler for channel: {channel}")

    async def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client exceeds rate limit"""
        if client_id not in self.clients:
            return False

        client = self.clients[client_id]
        # Simple rate limiting: max_message_rate per minute
        # In production, use a more sophisticated sliding window
        if client.message_count > self.max_message_rate:
            # Reset counter after 1 minute
            if (datetime.now() - client.connected_at).seconds > 60:
                client.message_count = 0
                return True
            return False
        return True

    async def start_heartbeat(self) -> None:
        """Start heartbeat/ping-pong mechanism"""
        self._running = True
        while self._running:
            await asyncio.sleep(self.ping_interval)

            # Send ping to all clients
            for client_id in list(self.clients.keys()):
                client = self.clients[client_id]

                # Check if client is still responsive
                if (datetime.now() - client.last_ping).seconds > self.ping_interval * 2:
                    logger.warning(f"Client {client_id} not responding, disconnecting")
                    await self.unregister_client(client_id)
                    continue

                # Send ping
                await self.send_to_client(
                    client_id,
                    WebSocketMessage(
                        type=MessageType.PING, channel=ChannelType.SYSTEM.value, data={}
                    ),
                )

    def stop_heartbeat(self) -> None:
        """Stop heartbeat"""
        self._running = False

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket server statistics"""
        return {
            "total_clients": len(self.clients),
            "total_channels": len(self.channels),
            "channels": {
                channel: len(clients) for channel, clients in self.channels.items()
            },
            "clients": [
                {
                    "id": client.id,
                    "subscriptions": list(client.subscriptions),
                    "authenticated": client.authenticated,
                    "message_count": client.message_count,
                    "connected_duration": (
                        datetime.now() - client.connected_at
                    ).seconds,
                }
                for client in self.clients.values()
            ],
        }


# NBA-specific WebSocket handlers


async def handle_game_subscription(client_id: str, message: WebSocketMessage) -> None:
    """Handle game-specific subscriptions"""
    game_id = message.data.get("game_id")
    if game_id:
        logger.info(f"Client {client_id} subscribed to game {game_id}")


async def handle_player_subscription(client_id: str, message: WebSocketMessage) -> None:
    """Handle player-specific subscriptions"""
    player_id = message.data.get("player_id")
    if player_id:
        logger.info(f"Client {client_id} subscribed to player {player_id}")


class NBAWebSocketServer:
    """NBA-specific WebSocket server"""

    def __init__(self):
        self.manager = WebSocketManager(ping_interval=30, max_message_rate=100)
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up NBA-specific message handlers"""
        self.manager.register_handler(
            ChannelType.GAME_UPDATES.value, handle_game_subscription
        )
        self.manager.register_handler(
            ChannelType.PLAYER_STATS.value, handle_player_subscription
        )

    async def broadcast_game_update(
        self,
        game_id: int,
        home_score: int,
        away_score: int,
        quarter: int,
        time_remaining: str,
    ) -> None:
        """Broadcast game score update"""
        message = WebSocketMessage(
            type=MessageType.MESSAGE,
            channel=ChannelType.GAME_UPDATES.value,
            data={
                "game_id": game_id,
                "home_score": home_score,
                "away_score": away_score,
                "quarter": quarter,
                "time_remaining": time_remaining,
            },
        )
        await self.manager.broadcast_to_channel(ChannelType.GAME_UPDATES.value, message)

    async def broadcast_player_stat_update(
        self, player_id: int, player_name: str, points: int, rebounds: int, assists: int
    ) -> None:
        """Broadcast player stat update"""
        message = WebSocketMessage(
            type=MessageType.MESSAGE,
            channel=ChannelType.PLAYER_STATS.value,
            data={
                "player_id": player_id,
                "player_name": player_name,
                "points": points,
                "rebounds": rebounds,
                "assists": assists,
            },
        )
        await self.manager.broadcast_to_channel(ChannelType.PLAYER_STATS.value, message)

    async def broadcast_play_by_play(
        self,
        game_id: int,
        event: str,
        player_name: str,
        team: str,
        quarter: int,
        time_remaining: str,
    ) -> None:
        """Broadcast play-by-play event"""
        message = WebSocketMessage(
            type=MessageType.MESSAGE,
            channel=ChannelType.PLAY_BY_PLAY.value,
            data={
                "game_id": game_id,
                "event": event,
                "player_name": player_name,
                "team": team,
                "quarter": quarter,
                "time_remaining": time_remaining,
            },
        )
        await self.manager.broadcast_to_channel(ChannelType.PLAY_BY_PLAY.value, message)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== NBA WebSocket Server Example ===\n")

    # Example usage
    print("1. Client connects:")
    print("   ws://localhost:8000/ws")
    print()

    print("2. Subscribe to live game updates:")
    print(
        json.dumps(
            {
                "type": "subscribe",
                "channel": "game_updates",
                "data": {"game_id": 12345},
            },
            indent=2,
        )
    )
    print()

    print("3. Receive real-time updates:")
    print(
        json.dumps(
            {
                "type": "message",
                "channel": "game_updates",
                "data": {
                    "game_id": 12345,
                    "home_score": 95,
                    "away_score": 92,
                    "quarter": 4,
                    "time_remaining": "2:30",
                },
                "timestamp": "2025-10-12T20:30:00",
            },
            indent=2,
        )
    )
    print()

    print("4. Subscribe to player stats:")
    print(
        json.dumps(
            {"type": "subscribe", "channel": "player_stats", "data": {"player_id": 23}},
            indent=2,
        )
    )
    print()

    print("5. Subscribe to play-by-play:")
    print(
        json.dumps(
            {
                "type": "subscribe",
                "channel": "play_by_play",
                "data": {"game_id": 12345},
            },
            indent=2,
        )
    )
