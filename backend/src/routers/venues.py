from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from src.schemas import VenueCreate, VenueResponse
from src.database import Session
from src.auth import CurrentUser
from src.models import Venue

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
