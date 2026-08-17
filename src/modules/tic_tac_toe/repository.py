from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import logger
from shared.models import EMatchStatus, Match

from .models import TicTacToeMatch


async def create_match(
    session: AsyncSession, player_id: int, opponent_id: int, grid_size: int
) -> int:
    """
    Creates a new tic-tac-toe match record in the database.

    Returns id of the created match.
    """

    logger.debug(
        f"tic: Creating a new match (player_id = {player_id}, opponent_id = {opponent_id}, "
        f"grid_size = {grid_size})..."
    )
    match_id: int = 0

    async with session.begin():
        parent_match: Match = Match(player_id=player_id)
        session.add(parent_match)

        # Flush pushes the record to Postgres temporarily to generate the auto-increment ID
        # without closing or committing the transaction yet.
        await session.flush()

        child_match: TicTacToeMatch = TicTacToeMatch(
            match_id=parent_match.match_id, opponent_id=opponent_id, grid_size=grid_size
        )
        session.add(child_match)

        match_id = parent_match.match_id

    logger.debug(f"tic: New match ({match_id}) created.")
    return match_id


async def update_match(
    session: AsyncSession, match_id: int, status: EMatchStatus, total_moves: int
) -> bool:
    """
    Updates an pending tic-tac-toe match record in the database.

    Returns true on success.
    """
    logger.debug(
        f"tic: Updating match ({match_id}) "
        f"with status ({status}) and total_moves ({total_moves})..."
    )

    async with session.begin():
        parent_match: Match | None = (
            await session.execute(select(Match).where(Match.match_id == match_id))
        ).scalar_one_or_none()

        child_match: TicTacToeMatch | None = (
            await session.execute(select(TicTacToeMatch).where(TicTacToeMatch.match_id == match_id))
        ).scalar_one_or_none()

        if not parent_match or not child_match:
            logger.warning(f"tic: Match ({match_id}) not found, update aborted.")
            return False

        if parent_match.status != EMatchStatus.PENDING:
            logger.error("tic: Only 'pending' matches can be updated.")
            return False

        parent_match.status = status
        child_match.total_moves = total_moves

    logger.debug(f"tic: Match ({match_id}) updated.")

    return True
