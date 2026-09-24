from typing import Annotated

from fastapi.security import OAuth2PasswordRequestForm

from src.schemas import UserCreate, UserResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import Session
from src.models.user_model import User
from src.auth import CurrentUser, hash_password, verify_password, create_access_token
from sqlalchemy import select

router = APIRouter(prefix= "/users", tags=["Users"])

@router.post("/token")
async def login_for_access_token(
    session: Session,
    form_data: OAuth2PasswordRequestForm = Depends(), 
):
    result = await session.execute(select(User).where(User.email == form_data.username.lower()))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    session: Session,
):
    email = user_in.email.lower()

    result = await session.execute(select(User).where(User.username == user_in.username))
    if result.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"user with username: {user_in.username} already exists")

    result = await session.execute(select(User).where(User.email == email))
    if result.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"user with email: {email} already exists")

    new_user = User(
        username = user_in.username,
        email = email,
        hashed_password = hash_password(user_in.password)
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user

@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: CurrentUser):
    return current_user
