from typing import Annotated, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from fastapi import Depends

from src.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo = True)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

Session = Annotated[AsyncSession, Depends(get_async_session)]