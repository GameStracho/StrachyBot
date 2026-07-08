from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base

class MatchHistory(Base):
    __tablename__ = "match_history"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'win', 'loss', 'timeout', 'draw')", name="valid_status"),
    )

    match_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    start_time: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now(timezone.utc))
    end_time: Mapped[Optional[datetime]] = mapped_column(nullable=True, default=None)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="pending")