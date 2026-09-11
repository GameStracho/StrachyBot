from sqlalchemy import BigInteger, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models import Base, Match
from shared.modules.trivia import ETriviaCategory, ETriviaDifficulty


class TriviaMatch(Base):
    __tablename__ = "trivia_match"

    match: Mapped[Match] = relationship()
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("match.id", ondelete="CASCADE"), primary_key=True
    )
    question: Mapped[str] = mapped_column(String, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String, nullable=False)

    # native_enum=True tells Postgres to create a custom ENUM data type
    category: Mapped[ETriviaCategory] = mapped_column(
        Enum(ETriviaCategory, native_enum=True), nullable=False, default=ETriviaCategory.ANY
    )

    # native_enum=True tells Postgres to create a custom ENUM data type
    difficulty: Mapped[ETriviaDifficulty] = mapped_column(
        Enum(ETriviaDifficulty, native_enum=True), nullable=False, default=ETriviaDifficulty.ANY
    )
