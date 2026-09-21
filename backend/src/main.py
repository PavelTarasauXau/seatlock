from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.database import engine, Base
from src.models import Venue, User, Seat

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/home")
def main():
    return "Hi"


