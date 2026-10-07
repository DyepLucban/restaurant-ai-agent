from __future__ import annotations
from datetime import UTC, datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connection import Base
from database.models.users import User

class Table(Base):
    __tablename__ = "tables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    table_number: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_reserved: Mapped[bool] = mapped_column(Boolean)
    reserved_date: Mapped[str] = mapped_column(VARCHAR, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    user: Mapped[User] = relationship(back_populates="table")