from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from src.schemas import EventCreate, EventResponse, EventSeatResponse
from src.database import Session
from src.auth import CurrentUser
from src.models import Event, Venue, EventSeat
from src.models.event_seat_model import EventSeatStatus

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


