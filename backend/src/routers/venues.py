from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from src.schemas import VenueCreate, VenueResponse, SeatCreate, SeatResponse
from src.database import Session
from src.auth import CurrentUser
from src.models import Venue, Seat

router = APIRouter(prefix="/venues", tags=["Venues"])

@router.post("", response_model=VenueResponse, status_code=status.HTTP_201_CREATED)
async def create_venue(
    venue_in: VenueCreate,
    session: Session,
    current_user: CurrentUser,
):
    result = await session.execute(
        select(Venue).where(Venue.name == venue_in.name, Venue.address == venue_in.address)
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Venue with name: {venue_in.name} and address {venue_in.address} already exists, change name or address",
        )

    new_venue = Venue(
        name=venue_in.name,
        address=venue_in.address,
        layout=venue_in.layout,
    )

    session.add(new_venue)
    await session.commit()
    await session.refresh(new_venue)
    return new_venue

@router.get("", response_model=list[VenueResponse])
async def get_venues(
    session: Session,
    current_user: CurrentUser,
):
    result = await session.execute(select(Venue))
    return result.scalars().all()

@router.get("/{venue_id}", response_model=VenueResponse)
async def get_venue_by_id(
    venue_id: int,
    session: Session,
    current_user: CurrentUser,
):
    venue = await session.get(Venue, venue_id)
    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Venue with id: {venue_id} doesn't exist",
        )
    return venue

@router.post("/{venue_id}/seats", response_model=list[SeatResponse], status_code=status.HTTP_201_CREATED)
async def create_seats(
    venue_id: int,
    seats_in: list[SeatCreate],
    session: Session,
    current_user: CurrentUser,
):
    venue = await session.get(Venue, venue_id)
    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected venue does not exist",
        )

    new_seats = [
        Seat(venue_id=venue_id, section=s.section, row_number=s.row_number, seat_number=s.seat_number, seat_type=s.seat_type)
        for s in seats_in
    ]

    session.add_all(new_seats)
    await session.commit()
    for seat in new_seats:
        await session.refresh(seat)
    return new_seats

@router.get("/{venue_id}/seats", response_model=list[SeatResponse], status_code=status.HTTP_200_OK)
async def get_seats(
    venue_id: int, 
    session: Session,
    current_user: CurrentUser,
):
    venue = await session.get(Venue, venue_id)
    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected venue does not exist",
        )

    return venue.seats
