from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Match, EMatchStatus
import shared.console as console
from .models import TriviaMatch, ETriviaCategory, ETriviaDifficulty

async def create_match(
        session: AsyncSession, player_id: int, category: ETriviaCategory, difficulty: ETriviaDifficulty,
        question: str, correct_answer: str) -> int:
    """
    Creates a new trivia match record in the database.
    
    Returns id of the created match.
    """

    console.log_debug((
        f"trivia: Creating a new match (player_id = {player_id}, category = {category}, difficulty = {difficulty}, "
        f"question = {question}, correct_answer = {correct_answer})..."
    ))

    match_id: int = 0

    async with session.begin():
        parent_match: Match = Match(player_id=player_id)
        session.add(parent_match)

        # Flush pushes the record to Postgres temporarily to generate the auto-increment ID
        # without closing or committing the transaction yet.
        await session.flush()

        child_match: TriviaMatch = TriviaMatch(
            match_id=parent_match.match_id,
            category=category,
            difficulty=difficulty,
            question=question,
            correct_answer=correct_answer
        )
        session.add(child_match)

        match_id = parent_match.match_id

    console.log_debug(f"trivia: New match ({match_id}) created.")
    return match_id


async def update_match(session: AsyncSession, match_id: int, status: EMatchStatus) -> bool:
    """
    Updates an pending trivia match record in the database.

    Returns true on success.
    """
    if status == EMatchStatus.PENDING:
        console.log_warning(f"trivia: Cannot update match status to {status}.")
        return False

    console.log_debug(f"trivia: Updating match ({match_id}) with status ({status})...")

    async with session.begin():
        match: Match | None = (await session.execute(
            select(Match).where(Match.match_id == match_id)
        )).scalar_one_or_none()

        if not match:
            console.log_warning(f"trivia: Match ({match_id}) not found, update aborted.")
            return False

        if match.status != EMatchStatus.PENDING:
            console.log_error("trivia: Only 'pending' matches can be updated.")
            return False

        match.status = status

    console.log_debug(f"trivia: Match ({match_id}) updated.")
    return True
