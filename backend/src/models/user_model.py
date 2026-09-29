from datetime import datetime


from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, )
    username: Mapped[str] = mapped_column(String(30), unique=True, index = True)
    # Пароль необязателен: у пользователей, вошедших только через Google, его нет
    hashed_password: Mapped[str | None] = mapped_column(String(100))
    # sub из Google id_token — стабильный идентификатор аккаунта Google
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
