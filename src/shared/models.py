from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import BigInteger, Enum, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _time_without_timezone() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


# Base class for models to inherit from
class Base(DeclarativeBase):
    pass


class EMatchStatus(PyEnum):
    PENDING = "Pending"
    WIN = "Win"
    LOSS = "Loss"
    TIMEOUT = "Timeout"
    DRAW = "Draw"
    SURRENDER = "Surrender"

    def __str__(self) -> str:
        return self.value


class Match(Base):
    __tablename__ = "match"

    match_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    start_time: Mapped[datetime] = mapped_column(nullable=False, default=_time_without_timezone)
    end_time: Mapped[datetime | None] = mapped_column(
        nullable=True, default=None, onupdate=_time_without_timezone
    )

    # native_enum=True tells Postgres to create a custom ENUM data type
    status: Mapped[EMatchStatus] = mapped_column(
        Enum(EMatchStatus, native_enum=True), nullable=False, default=EMatchStatus.PENDING
    )


class CommandLog(Base):
    __tablename__ = "command_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    command_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=_time_without_timezone)
