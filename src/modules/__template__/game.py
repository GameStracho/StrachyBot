from shared import models, types


class Game:
    _match_id: int
    _status: models.EMatchStatus
    _player: types.User

    def __init__(self, player: types.User) -> None:
        self._match_id = -1
        self._status = models.EMatchStatus.PENDING
        self._player = player

    def __str__(self) -> str:
        return (
            f"Game (match_id = {self._match_id}, status = {self._status}, player = {self._player})"
        )

    @property
    def match_id(self) -> int:
        return self._match_id

    @property
    def status(self) -> models.EMatchStatus:
        return self._status

    @property
    def player(self) -> types.User:
        return self._player

    async def start(self) -> None:
        pass

    async def _update_db_record(self) -> None:
        pass

    async def handle_timeout(self) -> None:
        self._status = models.EMatchStatus.TIMEOUT

    async def handle_surrender(self) -> None:
        self._status = models.EMatchStatus.SURRENDER
