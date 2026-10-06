from fastapi import APIRouter, HTTPException, status
from src.schemas import HoldResponse
from src.database import Session
from src.auth import CurrentUser
from src.models import Hold, EventSeat, EventSeatStatus, HoldStatus
from sqlalchemy import select
from datetime import datetime, timezone

router = APIRouter(prefix="/holds", tags=["Holds"])

@router.get("/me", response_model = list[HoldResponse], status_code=status.HTTP_200_OK)
async def get_holds(
    session: Session,
    current_user: CurrentUser,
):
    
    result = await session.execute(select(Hold).where(Hold.user_id == current_user.id))
    holds = await session.scalars(
    select(Hold)
    .where(
        Hold.user_id == current_user.id,
        Hold.status == HoldStatus.ACTIVE,
        Hold.expires_at > datetime.now(timezone.utc),
    )
    .order_by(Hold.expires_at)
    )
    return holds.all()


@router.delete("/{hold_id}", response_model=HoldResponse)
async def release_hold(hold_id: int, session: Session, current_user: CurrentUser):
    
    hold = await session.get(Hold, hold_id)
    if hold is None or hold.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hold not found")

    event_seat = await session.scalar(
        select(EventSeat).where(EventSeat.id == hold.event_seat_id).with_for_update()
    )

    await session.refresh(hold)

    if hold.status != HoldStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Hold is no longer active")

    hold.status = HoldStatus.RELEASED
    event_seat.status = EventSeatStatus.AVAILABLE
    await session.commit()
    return hold
