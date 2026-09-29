from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select

from src.database import Session
from src.oauth import oauth
from src.models.user_model import User
from src.auth import create_access_token

router = APIRouter(prefix="/auth/google", tags=["Google Auth"])

@router.get("/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/callback", name="google_callback")
async def google_callback(request: Request, session: Session):
    token = await oauth.google.authorize_access_token(request)
    user_info = token["userinfo"]

    if not user_info.get("email_verified"):
        raise HTTPException(status_code=400, detail="Email не подтверждён в Google")

    google_id = user_info["sub"]
    email = user_info["email"].lower()

    result = await session.execute(select(User).where(User.google_id == google_id))
    user = result.scalars().first()

    if user is None:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if user is not None:
            user.google_id = google_id
        else:
            username = email.split("@")[0]
            user = User(
                username=username,
                email=email,
                google_id=google_id,
                hashed_password=None,
            )
            session.add(user)

        await session.commit()
        await session.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
