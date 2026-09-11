from fastapi import APIRouter, HTTPException, status

from api.dependencies import DBSession
from shared import logger, models
from shared.modules.trivia import StartRequest, TriviaResponse

from . import repository
from .api import api_manager

router = APIRouter(prefix="/games/trivia", tags=["Trivia"])


@router.post("/start", response_model=TriviaResponse, status_code=status.HTTP_201_CREATED)
async def start_game(payload: StartRequest, session: DBSession) -> TriviaResponse:
    """Fetch a trivia question from OpenTDB and create a new match record."""
    question = await api_manager.get_question(
        category=payload.category, difficulty=payload.difficulty
    )

    match_id = await repository.create_match(
        session=session,
        player_id=payload.user_id,
        category=question.category,
        difficulty=question.difficulty,
        question=question.question,
        correct_answer=question.correct_answer,
    )

    logger.info(
        f"trivia: New match ({match_id}) started for player {payload.user_id}. Question: {question}"
    )

    return TriviaResponse(
        match_id=match_id,
        status=models.EMatchStatus.PENDING,
        player_id=payload.user_id,
        category=question.category,
        difficulty=question.difficulty,
        question=question.question,
        correct_answer=question.correct_answer,
        incorrect_answers=question.incorrect_answers,
    )


@router.patch("/{match_id}/answer", response_model=TriviaResponse)
async def submit_answer(match_id: int, answer: str, session: DBSession) -> TriviaResponse:
    """Submit an answer for a trivia match."""
    db_record = await repository.get_match_by_id(session=session, match_id=match_id)

    if not db_record or db_record.match.status != models.EMatchStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Match not found or already finished.",
        )

    is_correct = answer == db_record.correct_answer
    new_status = models.EMatchStatus.WIN if is_correct else models.EMatchStatus.LOSS

    logger.info(
        f"trivia: {'Correct' if is_correct else 'Incorrect'} answer '{answer}' "
        f"submitted for match ({match_id}) by player {db_record.match.player_id}."
    )

    await repository.update_match(session=session, match_id=match_id, status=new_status)

    return TriviaResponse(
        match_id=match_id,
        status=new_status,
        player_id=db_record.match.player_id,
        category=db_record.category,
        difficulty=db_record.difficulty,
        question=db_record.question,
        correct_answer=db_record.correct_answer,
        incorrect_answers=[],
    )


@router.patch("/{match_id}/timeout")
async def handle_timeout(match_id: int, session: DBSession) -> None:
    """Mark a trivia match as timed out."""
    db_record = await repository.get_match_by_id(session=session, match_id=match_id)

    if not db_record or db_record.match.status != models.EMatchStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Match not found or already finished.",
        )

    logger.info(f"trivia: Match ({match_id}) timed out.")
    await repository.update_match(
        session=session, match_id=match_id, status=models.EMatchStatus.TIMEOUT
    )
