import asyncio
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI

from src.config import settings
from src.database import engine, Base
from src.models import Venue, User, Seat
from src.routers import router as user_router, google_router, venue_router, event_router, hold_router, booking_router, payment_router, fake_provider_router
from src.services import run_hold_expiration_loop
from starlette.middleware.sessions import SessionMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        engine.echo = False
        #await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        engine.echo = True

    expiration_task = asyncio.create_task(
        run_hold_expiration_loop(settings.hold_expiration_interval_seconds)
    )
    yield
    expiration_task.cancel()
    with suppress(asyncio.CancelledError):
        await expiration_task

app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(google_router)
app.include_router(venue_router)
app.include_router(event_router)
app.include_router(hold_router)
app.include_router(booking_router)
app.include_router(payment_router)
if settings.enable_fake_provider:
    app.include_router(fake_provider_router)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key.get_secret_value())

@app.get("/home")
def main():
    return "Hi"