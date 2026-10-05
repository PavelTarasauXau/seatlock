import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_maker
from src.models import EventSeat, Hold
from src.models.event_seat_model import EventSeatStatus
from src.models.hold_model import HoldStatus

logger = logging.getLogger(__name__)


async def release_expired_hold(session: AsyncSession, event_seat: EventSeat) -> bool:
    """Expire the seat's active hold if its time is up. The seat row must already be locked FOR UPDATE."""
    hold = await session.scalar(
        select(Hold).where(
            Hold.event_seat_id == event_seat.id,
            Hold.status == HoldStatus.ACTIVE,
            Hold.expires_at <= datetime.now(timezone.utc),
        )
    )
    if hold is None:
        return False

    hold.status = HoldStatus.EXPIRED
    event_seat.status = EventSeatStatus.AVAILABLE
    await session.flush()
    return True


async def expire_holds(session: AsyncSession) -> int:
    """Mark all overdue active holds as expired and make their seats available again."""
    now = datetime.now(timezone.utc)

    # Lock seats first (same order as create_hold) and skip ones currently locked by a request
    result = await session.execute(
        select(EventSeat.id)
        .join(Hold, Hold.event_seat_id == EventSeat.id)
        .where(Hold.status == HoldStatus.ACTIVE, Hold.expires_at <= now)
        .order_by(EventSeat.id)
        .with_for_update(of=EventSeat, skip_locked=True)
    )
    seat_ids = result.scalars().all()
    if not seat_ids:
        return 0

    await session.execute(
        update(Hold)
        .where(
            Hold.event_seat_id.in_(seat_ids),
            Hold.status == HoldStatus.ACTIVE,
            Hold.expires_at <= now,
        )
        .values(status=HoldStatus.EXPIRED)
    )
    await session.execute(
        update(EventSeat)
        .where(EventSeat.id.in_(seat_ids), EventSeat.status == EventSeatStatus.HELD)
        .values(status=EventSeatStatus.AVAILABLE)
    )
    return len(seat_ids)


async def run_hold_expiration_loop(interval_seconds: int) -> None:
    while True:
        try:
            async with async_session_maker() as session:
                expired = await expire_holds(session)
                await session.commit()
            if expired:
                logger.info("Expired %d hold(s)", expired)
        except Exception:
            logger.exception("Hold expiration failed")
        await asyncio.sleep(interval_seconds)
