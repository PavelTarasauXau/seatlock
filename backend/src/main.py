from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.database import engine, Base
from src.models import Venue, User, Seat
from src.routers import router as user_router

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

@app.get("/home")
def main():
    return "Hi"


