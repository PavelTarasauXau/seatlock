from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from src.schemas import EventCreate, EventResponse, EventSeatResponse, HoldResponse
from src.database import Session
from src.auth import CurrentUser
from src.models import Event, Venue, EventSeat, Hold
from src.models.event_seat_model import EventSeatStatus
from src.services import release_expired_hold

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("", response_model=list[EventResponse])
async def get_events(
    session: Session,
    current_user: CurrentUser,
):
    events = await session.scalars(select(Event))
    return events.all()

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_in: EventCreate,
    session: Session,
    current_user: CurrentUser,
):
    venue = await session.get(Venue, event_in.venue_id)
    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected venue does not exist",
        )

    result = await session.execute(select(Event).where(Event.title == event_in.title))
    existing_event = result.scalars().first()

    if existing_event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event with selected title already exists",
        )

    if not venue.seats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected venue has no seats",
        )

    missing_types = {seat.seat_type for seat in venue.seats} - event_in.prices.keys()
    if missing_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No price for seat types: {', '.join(t.value for t in missing_types)}",
        )

    new_event = Event(
        venue_id=event_in.venue_id,
        title=event_in.title,
        starts_at=event_in.starts_at,
        hold_ttl_seconds=event_in.hold_ttl_seconds,
    )

    session.add(new_event)
    await session.flush()

    event_seats = []
    for seat in venue.seats:
        event_seats.append(
            EventSeat(
            event_id=new_event.id,
            seat_id=seat.id,
            price=event_in.prices[seat.seat_type],
            status=EventSeatStatus.AVAILABLE,
        ))

    session.add_all(event_seats)
    await session.commit()
    await session.refresh(new_event)
    return new_event

@router.get("/{event_id}", response_model=EventResponse)
async def get_event_by_id(
    event_id: int,
    session: Session,
    current_user: CurrentUser,
):
    event = await session.get(Event, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id: {event_id} doesn't exist",
        )
    return event

@router.get("/{event_id}/seats", response_model=list[EventSeatResponse], status_code=status.HTTP_200_OK)
async def get_event_seats(
    event_id: int,
    session: Session,
    current_user: CurrentUser,
):

    event = await session.get(Event, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event does not exist",
        ) 

    result = await session.execute(select(EventSeat).where(EventSeat.event_id == event_id))
    event_seats = result.scalars().all()
    return event_seats

@router.post("/{event_id}/seats/{event_seat_id}/hold", response_model=HoldResponse, status_code=status.HTTP_201_CREATED)
async def create_hold(
    event_id: int,
    event_seat_id: int,
    session: Session,
    current_user: CurrentUser,
):
    event = await session.get(Event, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event does not exist",
        )

    result = await session.execute(
        select(EventSeat)
        .where(EventSeat.id == event_seat_id, EventSeat.event_id == event_id)
        .with_for_update()
    )
    event_seat = result.scalars().first()
    if event_seat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seat not found for this event",
        )

    if event_seat.status == EventSeatStatus.HELD:
        await release_expired_hold(session, event_seat)

    if event_seat.status != EventSeatStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This seat is not available",
        )

    event_seat.status = EventSeatStatus.HELD

    new_hold = Hold(
        event_seat_id=event_seat.id,
        user_id=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=event.hold_ttl_seconds),
    )

    session.add(new_hold)
    await session.commit()
    await session.refresh(new_hold)
    return new_hold
