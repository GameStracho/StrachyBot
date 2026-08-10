from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class TicTacToeMatch(Base):
    __tablename__ = "tic_tac_toe_match"
    __table_args__ = (
        CheckConstraint("grid_size BETWEEN 3 AND 5", name="valid_grid_size"),
        CheckConstraint(
            "total_moves BETWEEN 0 AND grid_size * grid_size", name="valid_total_moves"
        ),
    )

    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("match.match_id", ondelete="CASCADE"), primary_key=True
    )
    opponent_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_moves: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    grid_size: Mapped[int] = mapped_column(Integer, nullable=False)
