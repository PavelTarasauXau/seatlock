import asyncio
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.config import settings
from src.database import engine, Base
from src.models import Venue, User, Seat
from src.routers import router as user_router, google_router, venue_router, event_router, hold_router, booking_router, payment_router, fake_provider_router
from src.services import run_hold_expiration_loop
from starlette.middleware.sessions import SessionMiddleware
from src.exceptions import AppError
from src.redis_client import redis
from src.rate_limiter import RateLimiterMiddleware

RATE_LIMITER = 5
WINDOW_SECONDS = 10

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
    await redis.aclose()

app = FastAPI(lifespan=lifespan)

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

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
#app.add_middleware(RateLimiterMiddleware, limit=RATE_LIMITER, window=WINDOW_SECONDS)

@app.exception_handler(AppError)
async def app_err_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.get("/home")
def main():
    return "Hi" 