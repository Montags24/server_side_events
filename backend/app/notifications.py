import asyncio
import os
from collections.abc import AsyncIterator

from redis.asyncio import Redis

from .schemas import Notification

REDIS_URL = os.getenv("REDIS_URL")
REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "notifications")

redis_client: Redis | None = None
notification_subscribers: set[asyncio.Queue[str]] = set()


async def connect_notifications() -> None:
    global redis_client

    if REDIS_URL is None:
        return

    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    await redis_client.ping()


async def close_notifications() -> None:
    global redis_client

    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None


async def publish_notification(notification: Notification) -> None:
    payload = notification.model_dump_json()

    if redis_client is not None:
        await redis_client.publish(REDIS_CHANNEL, payload)
        return

    for subscriber in tuple(notification_subscribers):
        subscriber.put_nowait(payload)


async def subscribe_notifications() -> AsyncIterator[str]:
    if redis_client is not None:
        async with redis_client.pubsub() as pubsub:
            await pubsub.subscribe(REDIS_CHANNEL)

            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield message["data"]

        return

    queue: asyncio.Queue[str] = asyncio.Queue()
    notification_subscribers.add(queue)

    try:
        while True:
            yield await queue.get()
    finally:
        notification_subscribers.discard(queue)
