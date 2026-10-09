from datetime import datetime, timezone

from typing import Annotated
import uuid
from fastapi import APIRouter, HTTPException, status, Header
from sqlalchemy import select

from src.schemas import BookingResponse, BookingCreate, PaymentResponse
from src.database import Session
from src.auth import CurrentUser
from src.models import Hold, HoldStatus, EventSeat, EventSeatStatus, Booking, BookingItem, BookingStatus, Payment, PaymentStatus

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_in: BookingCreate,
    session: Session,
    current_user: CurrentUser,
):
    hold_ids = set(booking_in.hold_ids)
    holds_query = select(Hold).where(Hold.id.in_(hold_ids), Hold.user_id == current_user.id)

    holds = (await session.scalars(holds_query)).all()
    if len(holds) != len(hold_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holds not found",
        )

    seat_ids = [hold.event_seat_id for hold in holds]
    seats = (await session.scalars(
        select(EventSeat)
        .where(EventSeat.id.in_(seat_ids))
        .order_by(EventSeat.id)
        .with_for_update()
    )).all()

    holds = (await session.scalars(
        holds_query.execution_options(populate_existing=True)
    )).all()

    now = datetime.now(timezone.utc)
    if any(hold.status != HoldStatus.ACTIVE or hold.expires_at <= now for hold in holds):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Some holds are no longer active",
        )

    event_ids = {seat.event_id for seat in seats}
    if len(event_ids) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All seats must belong to the same event",
        )

    items = [BookingItem(event_seat_id=seat.id, price=seat.price) for seat in seats]
    booking = Booking(
        user_id=current_user.id,
        event_id=event_ids.pop(),
        total_price=sum(item.price for item in items),
        items=items,
    )
    session.add(booking)

    for hold in holds:
        hold.status = HoldStatus.CONVERTED
    for seat in seats:
        seat.status = EventSeatStatus.BOOKED

    await session.commit()
    await session.refresh(booking, ["created_at"])
    return booking

@router.get("/me", response_model=list[BookingResponse], status_code=status.HTTP_200_OK)
async def get_bookings(
    session: Session,
    current_user: CurrentUser,    
):

    result = await session.execute(
        select(Booking).where(Booking.user_id == current_user.id)
        .order_by(Booking.created_at.desc())
        )
    bookings = result.scalars().all()

    return bookings

@router.get("/{booking_id}", response_model=BookingResponse, status_code=status.HTTP_200_OK)
async def get_booking_by_id(
    booking_id: int,
    session: Session,
    current_user: CurrentUser,
):

    result = await session.execute(select(Booking).where(Booking.id == booking_id, Booking.user_id == current_user.id))
    booking = result.scalars().first()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    return booking

@router.post("/{booking_id}/cancel", response_model=BookingResponse, status_code=status.HTTP_200_OK)
async def cancel_booking(
    booking_id: int,
    session: Session,
    current_user: CurrentUser,
):

    booking = await session.scalar(
        select(Booking)
        .where(Booking.id == booking_id, Booking.user_id == current_user.id)
        .with_for_update()
    )

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if booking.status != BookingStatus.PENDING_PAYMENT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only unpaid bookings can be cancelled",
        )

    pending_payment = await session.scalar(
        select(Payment).where(Payment.booking_id == booking_id, Payment.status == PaymentStatus.PENDING)
    )
    if pending_payment is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Booking has a payment in progress",
        )

    seat_ids = [item.event_seat_id for item in booking.items]
    seats = (await session.scalars(
        select(EventSeat)
        .where(EventSeat.id.in_(seat_ids))
        .order_by(EventSeat.id)
        .with_for_update()
    )).all()

    booking.status = BookingStatus.CANCELLED
    for seat in seats:
        seat.status = EventSeatStatus.AVAILABLE

    await session.commit()
    return booking


@router.post("/{booking_id}/pay", response_model=PaymentResponse, status_code=status.HTTP_200_OK)
async def pay_booking(
    booking_id: int,
    session: Session,
    current_user: CurrentUser,
    idempotency_key: Annotated[str, Header()]
):

    result = await session.execute(
        select(Booking)
        .where(Booking.id == booking_id, Booking.user_id == current_user.id)
        .with_for_update()
    )
    booking = result.scalar_one_or_none()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    existing_payment = await session.scalar(
        select(Payment).where(Payment.idempotency_key == idempotency_key)
    )
    if existing_payment is not None:
        if existing_payment.booking_id != booking_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency key is already used for another booking",
            )
        return existing_payment

    if booking.status != BookingStatus.PENDING_PAYMENT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Booking is not awaiting payment",
        )

    pending_payment = await session.scalar(
        select(Payment).where(Payment.booking_id == booking_id, Payment.status == PaymentStatus.PENDING)
    )
    if pending_payment is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment is already processing",
        )

    new_payment = Payment(
        booking_id=booking_id,
        amount=booking.total_price,
        provider="fake",
        provider_ref=str(uuid.uuid4()),
        idempotency_key=idempotency_key,
    )

    session.add(new_payment)
    await session.commit()
    await session.refresh(new_payment)
    return new_payment

    
    