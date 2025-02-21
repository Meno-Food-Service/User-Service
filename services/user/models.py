from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean
from core.database.user import UserBASE
from datetime import datetime


class UserModel(UserBASE):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, index=True, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="Пользователь")

    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())
