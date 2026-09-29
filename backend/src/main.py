from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.config import settings
from src.database import engine, Base
from src.models import Venue, User, Seat
from src.routers import router as user_router, google_router
from starlette.middleware.sessions import SessionMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        engine.echo = False
        #await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        engine.echo = True
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(google_router)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key.get_secret_value())

@app.get("/home")
def main():
    return "Hi"