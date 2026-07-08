from sqlalchemy import BigInteger, ForeignKey, String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base

class WordleMatch(Base):
    __tablename__ = "wordle_match"
    __table_args__ = (
        CheckConstraint("guesses_count BETWEEN 0 AND 6", name="valid_guesses"),
    )

    match_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("match_history.match_id", ondelete="CASCADE"), primary_key=True)
    secret_word: Mapped[str] = mapped_column(String(5), nullable=False)
    guesses_count: Mapped[int] = mapped_column(nullable=False)
