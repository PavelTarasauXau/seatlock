from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import NotFoundError, ConflictError
from src.models import Booking, BookingStatus, EventSeat, EventSeatStatus, Payment, PaymentStatus


async def _get_booking_for_update(
        session: AsyncSession, 
        booking_id: int, 
        user_id: int
    ) -> Booking:
    """Find the user's booking and lock it. Status is checked by the caller."""
    booking = await session.scalar(
        select(Booking)
        .where(Booking.id == booking_id, Booking.user_id == user_id)
        .with_for_update()
    )
    if booking is None:
        raise NotFoundError("Booking not found")
    return booking


async def _lock_seats(
        session: AsyncSession, 
        seat_ids: Iterable[int]
    ) -> list[EventSeat]:
    """Lock seats in id order, so concurrent transactions can't deadlock."""
    seats = await session.scalars(
        select(EventSeat)
        .where(EventSeat.id.in_(seat_ids))
        .order_by(EventSeat.id)
        .with_for_update()
    )
    return list(seats.all())


async def _ensure_no_pending_payment(
        session: AsyncSession, 
        booking_id: int, 
        detail: str
        ) -> None:
    pending_payment = await session.scalar(
        select(Payment).where(Payment.booking_id == booking_id, Payment.status == PaymentStatus.PENDING)
    )
    if pending_payment is not None:
        raise ConflictError(detail)


async def cancel_booking(
        session: AsyncSession, 
        booking_id: int, 
        user_id: int
        ) -> Booking:
    booking = await _get_booking_for_update(session, booking_id, user_id)

    if booking.status != BookingStatus.PENDING_PAYMENT:
        raise ConflictError("Only unpaid bookings can be cancelled")

    await _ensure_no_pending_payment(session, booking.id, "Booking has a payment in progress")

    seats = await _lock_seats(session, [item.event_seat_id for item in booking.items])

    booking.status = BookingStatus.CANCELLED
    for seat in seats:
        seat.status = EventSeatStatus.AVAILABLE

    await session.commit()
    return booking
