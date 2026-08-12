import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False)
    method: Mapped[str] = mapped_column(String(10), default="GET")
    expected_status: Mapped[int] = mapped_column(Integer, default=200)
    interval_seconds: Mapped[int] = mapped_column(Integer, default=30)
    timeout: Mapped[float] = mapped_column(Float, default=5.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)