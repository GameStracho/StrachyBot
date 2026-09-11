from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shared import logger
from shared.models import EMatchStatus, Match
from shared.modules.trivia import ETriviaCategory, ETriviaDifficulty

from .models import TriviaMatch


async def get_match_by_id(
    session: AsyncSession,
    match_id: int,
) -> TriviaMatch | None:
    """Fetches a trivia match by its unique ID."""
    result = await session.execute(
        select(TriviaMatch)
        .options(joinedload(TriviaMatch.match))
        .where(TriviaMatch.match_id == match_id)
    )
    return result.scalar_one_or_none()


async def create_match(
    session: AsyncSession,
    player_id: int,
    category: ETriviaCategory,
    difficulty: ETriviaDifficulty,
    question: str,
    correct_answer: str,
) -> int:
    """
    Creates a new trivia match record in the database.

    Returns id of the created match.
    """
    logger.debug(
        f"trivia: Creating a new match (player_id = {player_id}, category = {category}, "
        f"difficulty = {difficulty}, question = {question}, "
        f"correct_answer = {correct_answer})..."
    )

    parent_match: Match = Match(player_id=player_id)
    session.add(parent_match)

    # Flush pushes the record to Postgres temporarily to generate the auto-increment ID
    # without closing or committing the transaction yet.
    await session.flush()

    child_match: TriviaMatch = TriviaMatch(
        match_id=parent_match.id,
        category=category,
        difficulty=difficulty,
        question=question,
        correct_answer=correct_answer,
    )
    session.add(child_match)

    match_id = parent_match.id
    logger.debug(f"trivia: New match ({match_id}) created.")
    return match_id


async def update_match(session: AsyncSession, match_id: int, status: EMatchStatus) -> bool:
    """
    Updates a pending trivia match record in the database.

    Returns true on success.
    """
    logger.debug(f"trivia: Updating match ({match_id}) with status ({status})...")

    parent_match: Match | None = (
        await session.execute(select(Match).where(Match.id == match_id))
    ).scalar_one_or_none()

    if not parent_match:
        logger.warning(f"trivia: Match ({match_id}) not found, update aborted.")
        return False

    if parent_match.status != EMatchStatus.PENDING:
        logger.error("trivia: Only 'pending' matches can be updated.")
        return False

    parent_match.status = status
    logger.debug(f"trivia: Match ({match_id}) updated.")
    return True
