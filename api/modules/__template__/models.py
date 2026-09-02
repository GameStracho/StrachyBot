from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models import Base, Match


class GameMatch(Base):
    __tablename__ = "game_match"
    __table_args__ = (CheckConstraint("moves_count BETWEEN 0 AND 6", name="valid_guesses"),)

    match: Mapped[Match] = relationship()
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("match.id", ondelete="CASCADE"), primary_key=True
    )
    word: Mapped[str] = mapped_column(String(5), nullable=False)
    moves_count: Mapped[int] = mapped_column(nullable=False, default=0)
