from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Event
from src.redis_client import redis
from src.schemas import EventResponse

EVENTS_CACHE_KEY = "events:list"
EVENTS_CACHE_TTL = 60

events_adapter = TypeAdapter(list[EventResponse])


async def get_events_cached(session: AsyncSession) -> list[EventResponse]:
    """Cache-aside: return the list from Redis, or load it from the DB and cache it."""
    cached = await redis.get(EVENTS_CACHE_KEY)
    if cached is not None:
        return events_adapter.validate_json(cached)

    events = (await session.scalars(select(Event))).all()
    result = events_adapter.validate_python(events, from_attributes=True)
    await redis.set(EVENTS_CACHE_KEY, events_adapter.dump_json(result), ex=EVENTS_CACHE_TTL)
    return result


async def invalidate_events_cache() -> None:
    """Call after any committed change to events, so the next read reloads them."""
    await redis.delete(EVENTS_CACHE_KEY)
