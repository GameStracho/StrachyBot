from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import ARRAY, BigInteger, CheckConstraint, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models import Base


class ESonglessCategory(PyEnum):
    ALL = "All"
    POP = "Pop"
    HIP_HIP = "Hip-Hop"
    ROCK = "Rock"

    def __str__(self) -> str:
        return self.value


class SonglessMatch(Base):
    __tablename__ = "songless_match"
    __table_args__ = (CheckConstraint("guesses_count BETWEEN 0 AND 6", name="valid_guesses"),)

    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("match.match_id", ondelete="CASCADE"), primary_key=True
    )
    song_id: Mapped[int] = mapped_column(String(5), nullable=False)
    guesses_count: Mapped[int] = mapped_column(nullable=False, default=0)
    is_daily: Mapped[bool] = mapped_column(nullable=False, default=False)

    # native_enum=True tells Postgres to create a custom ENUM data type
    category: Mapped[ESonglessCategory] = mapped_column(
        Enum(ESonglessCategory, native_enum=True), nullable=False, default=ESonglessCategory.ALL
    )

    guesses: Mapped[list[str]] = mapped_column(ARRAY(String(5)), nullable=False, default=list)


class SonglessSong(Base):
    __tablename__ = "songless_song"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    title: Mapped[str] = mapped_column(String(), nullable=False)
    artist: Mapped[str] = mapped_column(String(), nullable=False)

    # native_enum=True tells Postgres to create a custom ENUM data type
    category: Mapped[ESonglessCategory] = mapped_column(
        Enum(ESonglessCategory, native_enum=True), nullable=False, default=ESonglessCategory.ALL
    )

    added_at: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.now(UTC).replace(tzinfo=None)
    )
