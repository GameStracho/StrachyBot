from datetime import datetime, timezone
from typing import Optional
from enum import Enum as PyEnum

from sqlalchemy import BigInteger, Enum
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


def _time_without_timezone() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class EMatchStatus(PyEnum):
    PENDING = "Pending"
    WIN = "Win"
    LOSS = "Loss"
    TIMEOUT = "Timeout"
    DRAW = "Draw"

class Match(Base):
    __tablename__ = "match"

    match_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    start_time: Mapped[datetime] = mapped_column(nullable=False, default=_time_without_timezone)
    end_time: Mapped[Optional[datetime]] = mapped_column(nullable=True, default=None, onupdate=_time_without_timezone)
    
    # native_enum=True tells Postgres to create a custom ENUM data type
    status: Mapped[EMatchStatus] = mapped_column(
        Enum(EMatchStatus, native_enum=True),
        nullable=False,
        default=EMatchStatus.PENDING
    )
