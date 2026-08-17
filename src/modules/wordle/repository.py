from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import logger
from shared.models import EMatchStatus, Match

from .models import WordleMatch


async def create_match(
    session: AsyncSession, player_id: int, secret_word: str, is_daily: bool
) -> int:
    """
    Creates a new wordle match record in the database.

    Returns id of the created match.
    """

    logger.debug(
        f"wordle: Creating a new match (player_id = {player_id}, secret_word = {secret_word})..."
    )
    match_id: int = 0

    async with session.begin():
        parent_match: Match = Match(player_id=player_id)
        session.add(parent_match)

        # Flush pushes the record to Postgres temporarily to generate the auto-increment ID
        # without closing or committing the transaction yet.
        await session.flush()

        child_match: WordleMatch = WordleMatch(
            match_id=parent_match.match_id, secret_word=secret_word, is_daily=is_daily
        )
        session.add(child_match)

        match_id = parent_match.match_id

    logger.debug(f"wordle: New match ({match_id}) created.")
    return match_id


async def update_match(
    session: AsyncSession,
    match_id: int,
    status: EMatchStatus,
    guesses_count: int,
    guesses: list[str],
) -> bool:
    """
    Updates an pending wordle match record in the database.

    Returns true on success.
    """
    logger.debug(
        f"wordle: Updating match ({match_id}) "
        f"with status ({status}) and {guesses_count} guesses ({guesses})..."
    )

    async with session.begin():
        parent_match: Match | None = (
            await session.execute(select(Match).where(Match.match_id == match_id))
        ).scalar_one_or_none()

        child_match: WordleMatch | None = (
            await session.execute(select(WordleMatch).where(WordleMatch.match_id == match_id))
        ).scalar_one_or_none()

        if not parent_match or not child_match:
            logger.error(f"wordle: Match ({match_id}) not found, update aborted.")
            return False

        if parent_match.status != EMatchStatus.PENDING:
            logger.error("wordle: Only 'pending' matches can be updated.")
            return False

        parent_match.status = status
        child_match.guesses_count = guesses_count
        child_match.guesses = guesses

    logger.debug(f"wordle: Match ({match_id}) updated.")

    return True


async def has_played_daily_challenge(
    session: AsyncSession, player_id: int, target_date: date | None = None
) -> bool:
    """
    Checks whether a player has already started or played the daily challenge on a specific date.
    """
    if target_date is None:
        target_date = datetime.now(tz=UTC).date()

    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)

    wordle_matches = (
        select(func.count())
        .select_from(WordleMatch)
        .join(Match, WordleMatch.match_id == Match.match_id)
        .where(
            Match.player_id == player_id,
            WordleMatch.is_daily.is_(True),
            Match.start_time >= start_of_day,
            Match.start_time <= end_of_day,
        )
    )

    result = await session.execute(wordle_matches)
    count = result.scalar() or 0
    return count > 0
