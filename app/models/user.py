from .base import Base
from sqlalchemy.orm import (
    mapped_column, Mapped
)


class User(Base):
    user_id: Mapped[int] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column()
    password: Mapped[str] = mapped_column()


