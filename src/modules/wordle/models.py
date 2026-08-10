from sqlalchemy import ARRAY, BigInteger, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models import Base


class WordleMatch(Base):
    __tablename__ = "wordle_match"
    __table_args__ = (CheckConstraint("guesses BETWEEN 0 AND 6", name="valid_guesses"),)

    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("match.match_id", ondelete="CASCADE"), primary_key=True
    )
    secret_word: Mapped[str] = mapped_column(String(5), nullable=False)
    guesses_count: Mapped[int] = mapped_column(nullable=False, default=0)
    is_daily: Mapped[bool] = mapped_column(nullable=False, default=False)
    guesses: Mapped[list[str]] = mapped_column(ARRAY(String(5)), nullable=False, default=list)
