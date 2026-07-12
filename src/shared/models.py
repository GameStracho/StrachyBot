from datetime import datetime, timezone
from typing import Optional
from enum import Enum as PyEnum

from sqlalchemy import BigInteger, Enum
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base

class EMatchStatus(PyEnum):
    PENDING = "pending"
    WIN = "win"
    LOSS = "loss"
    TIMEOUT = "timeout"
    DRAW = "draw"

class Match(Base):
    __tablename__ = "match"

    match_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    start_time: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now(timezone.utc))
    end_time: Mapped[Optional[datetime]] = mapped_column(nullable=True, default=None, onupdate=datetime.now(timezone.utc))
    
    # native_enum=True tells Postgres to create a custom ENUM data type
    status: Mapped[EMatchStatus] = mapped_column(
        Enum(EMatchStatus, native_enum=True),
        nullable=False,
        default=EMatchStatus.PENDING
    )
