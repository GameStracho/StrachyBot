from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Match, EMatchStatus
import shared.console as console
from .models import WordleMatch

async def create_match(session: AsyncSession, player_id: int, secret_word: str) -> int:
    """
    Creates a new wordle match record in the database.
    
    Returns id of the created match.
    """

    console.log_debug(f"wordle: Creating a new match (player_id = {player_id}, secret_word = {secret_word})...")
    match_id: int = 0

    async with session.begin():
        parent_match: Match = Match(player_id=player_id)
        session.add(parent_match)

        # Flush pushes the record to Postgres temporarily to generate the auto-increment ID
        # without closing or committing the transaction yet.
        await session.flush()

        child_match: WordleMatch = WordleMatch(
            match_id=parent_match.match_id,
            secret_word=secret_word
        )
        session.add(child_match)

        match_id = parent_match.match_id

    console.log_debug(f"wordle: New match ({match_id}) created.")
    return match_id


async def update_match(session: AsyncSession, match_id: int, status: EMatchStatus, guesses: int) -> bool:
    """
    Updates an pending wordle match record in the database.

    Returns true on success.
    """

    console.log_debug(f"wordle: Updating match ({match_id}) with status ({status}) and guesses ({guesses})...")

    async with session.begin():
        parent_match: Match | None = await session.execute(
            select(Match).where(Match.match_id == match_id)
        ).scalar_one_or_none()

        child_match: WordleMatch | None = await session.execute(
            select(WordleMatch).where(WordleMatch.match_id == match_id)
        ).scalar_one_or_none()

        if not parent_match or not child_match:
            console.log_error(f"wordle: Match ({match_id}) not found, update aborted.")
            return False

        if parent_match.status != EMatchStatus.PENDING:
            console.log_error(f"wordle: Only 'pending' matches can be updated.")
            return False

        parent_match.status = status
        child_match.guesses = guesses

    console.log_debug(f"wordle: Match ({match_id}) updated.")

    return True
