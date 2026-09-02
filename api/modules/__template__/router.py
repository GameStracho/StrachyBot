from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared import logger, models
from shared.database import get_session

from . import repository, schemas
from .game import Game

router = APIRouter(prefix="/games/__template__", tags=["Template Game"])


@router.post("/start", response_model=schemas.GameResponse, status_code=status.HTTP_201_CREATED)
async def start_game(
    payload: schemas.StartRequest, session: AsyncSession = Depends(get_session)
) -> schemas.GameResponse:
    game = Game(player_id=payload.user_id, word="START")

    match_id = await repository.create_match(
        session=session, player_id=payload.user_id, word=game.word
    )

    return schemas.GameResponse(
        match_id=match_id,
        status=game.status,
        player_id=game.player_id,
        moves_count=0,
        word=game.word,
    )


@router.post("/{match_id}/move", response_model=schemas.GameResponse)
async def submit_move(
    match_id: int, session: AsyncSession = Depends(get_session)
) -> schemas.GameResponse:
    db_record = await repository.get_match_by_id(session=session, match_id=match_id)

    if not db_record or db_record.match.status != models.EMatchStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Match not found or already finished."
        )

    game = Game.from_db_record(record=db_record)
    game.submit_move()

    await repository.update_match(
        session=session, match_id=game.id, status=game.status, moves_count=game.moves_count
    )

    return schemas.GameResponse(
        match_id=game.id, status=game.status, player_id=game.player_id, moves_count=game.moves_count
    )


@router.patch("/{match_id}/timeout")
async def handle_timeout(match_id: int, session: AsyncSession = Depends(get_session)) -> None:
    db_record = await repository.get_match_by_id(session=session, match_id=match_id)

    if not db_record or db_record.match.status != models.EMatchStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Match not found or already finished."
        )

    game = Game.from_db_record(record=db_record)
    logger.info(f"Game {game} timed out.")

    await repository.update_match(
        session=session,
        match_id=game.id,
        status=models.EMatchStatus.TIMEOUT,
        moves_count=game.moves_count,
    )


@router.patch("/{match_id}/surrender")
async def handle_surrender(match_id: int, session: AsyncSession = Depends(get_session)) -> None:
    db_record = await repository.get_match_by_id(session=session, match_id=match_id)

    if not db_record or db_record.match.status != models.EMatchStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Match not found or already finished."
        )

    game = Game.from_db_record(record=db_record)
    logger.info(f"Game {game} surrendered.")

    await repository.update_match(
        session=session,
        match_id=game.id,
        status=models.EMatchStatus.SURRENDER,
        moves_count=game.moves_count,
    )
