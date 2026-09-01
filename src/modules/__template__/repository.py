from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import logger
from shared.models import EMatchStatus, Match

from .models import GameMatch


async def create_match(session: AsyncSession, player_id: int, word: str) -> int:
    """
    Creates a new GAME match record in the database.

    Returns id of the created match.
    """

    logger.debug(f"GAME: Creating a new match (player_id = {player_id}, word = {word})...")
    match_id: int = 0

    async with session.begin():
        parent_match: Match = Match(player_id=player_id)
        session.add(parent_match)

        # Flush pushes the record to Postgres temporarily to generate the auto-increment ID
        # without closing or committing the transaction yet.
        await session.flush()

        child_match: GameMatch = GameMatch(match_id=parent_match.id, word=word)
        session.add(child_match)

        match_id = parent_match.id

    logger.debug(f"GAME: New match ({match_id}) created.")
    return match_id


async def update_match(
    session: AsyncSession,
    match_id: int,
    status: EMatchStatus,
    moves_count: int,
) -> bool:
    """
    Updates an pending GAME match record in the database.

    Returns true on success.
    """
    logger.debug(
        f"GAME: Updating match ({match_id}) with status ({status}) and {moves_count} moves..."
    )

    async with session.begin():
        parent_match: Match | None = (
            await session.execute(select(Match).where(Match.id == match_id))
        ).scalar_one_or_none()

        child_match: GameMatch | None = (
            await session.execute(select(GameMatch).where(GameMatch.match_id == match_id))
        ).scalar_one_or_none()

        if not parent_match or not child_match:
            logger.error(f"GAME: Match ({match_id}) not found, update aborted.")
            return False

        if parent_match.status != EMatchStatus.PENDING:
            logger.error("GAME: Only 'pending' matches can be updated.")
            return False

        parent_match.status = status
        child_match.moves_count = moves_count

    logger.debug(f"GAME: Match ({match_id}) updated.")

    return True
