from __future__ import annotations

from types import SimpleNamespace, TracebackType
from typing import Any
from unittest.mock import AsyncMock

import discord

from shared import bot, models, types


class DummyStrachyBot(bot.StrachyBot):
    pass


class DummyUser(types.User):
    def __init__(self, user_id: int = 1, username: str = "Tester", is_bot: bool = False) -> None:
        super().__init__(
            id=user_id,
            name="Tester",
            display_name=username,
            display_avatar="example.com/avatar",
            mention=f"<@{user_id}>",
            is_bot=is_bot,
        )

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def mention(self) -> str:
        return self._mention

    @property
    def bot(self) -> bool:
        return self._is_bot

    @property
    def display_avatar(self) -> SimpleNamespace:  # type: ignore[override]
        return SimpleNamespace(url=self._display_avatar)


class DummyConnection:
    async def run_sync(self, fn: Any, *arg: Any, **kw: Any) -> Any:
        return None


class DummyTransaction:
    async def __aenter__(self) -> DummyConnection:
        return DummyConnection()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        return False


class DummyContextManager:
    def __init__(self, session: DummySession) -> None:
        self.session = session

    async def __aenter__(self) -> DummySession:
        return self.session

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        return False


class DummyResult:
    def __init__(self, value: Any = None, rowcount: int = 0) -> None:
        self._value = value
        self.rowcount = rowcount

    def scalar_one_or_none(self) -> Any:
        return self._value


class DummySession:
    def __init__(self, match: models.Match | None = None) -> None:
        self.match = match
        self.added: list[Any] = []
        self.flushed = False
        self.executed = False

    def begin(self) -> DummyContextManager:
        return DummyContextManager(self)

    def add(self, instance: object) -> None:
        self.added.append(instance)

    async def flush(self) -> None:
        self.flushed = True
        for obj in self.added:
            if hasattr(obj, "match_id") and getattr(obj, "match_id", None) is None:
                object.__setattr__(obj, "match_id", 1)

    async def commit(self) -> None:
        pass

    async def execute(self, *args: Any, **kwargs: Any) -> DummyResult:
        self.executed = True
        return DummyResult(self.match)


class DummyResponse:
    def __init__(self) -> None:
        self.edit_calls: list[dict[str, Any]] = []
        self.send_calls: list[tuple[Any, dict[str, Any]]] = []
        self.defer = AsyncMock()

    async def edit_message(self, **kwargs: Any) -> None:
        self.edit_calls.append(kwargs)

    async def send_message(self, *args: Any, **kwargs: Any) -> None:
        self.send_calls.append((args, kwargs))


class DummyInteraction(discord.Interaction):
    # Overriding fields for type-checker compatibility
    message: Any
    response: Any
    followup: Any
    user: Any

    def __init__(self, user: DummyUser) -> None:
        # Avoid running full discord.Interaction internal state machine logic during raw unit tests
        self.user = SimpleNamespace(
            id=user.id,
            display_name=user.display_name,
            name=user.name,
            mention=user.mention,
            display_avatar=SimpleNamespace(url=user.display_avatar),
            bot=user.is_bot,
        )
        self.response = SimpleNamespace(
            defer=AsyncMock(),
            send_message=AsyncMock(),
            edit_message=AsyncMock(),
            send_modal=AsyncMock(),
        )
        self.followup = SimpleNamespace(send=AsyncMock())
        self.original_response_message: discord.Message | None = None
        self._followup_sent: dict[str, Any] | None = None

    @property
    def client(self) -> Any:
        return DummyStrachyBot()

    async def defer(self, *, ephemeral: bool = False, thinking: bool = False) -> None:
        await self.response.defer()

    async def followup_send(self, **kwargs: Any) -> None:
        self._followup_sent = kwargs

    async def original_response(self) -> Any:
        return self.original_response_message


class TestError(Exception):
    def __init__(self, *args: Any) -> None:
        super().__init__(*args)


async def dummy_execute_db_operation(target: Any, db_func: Any, *args: Any, **kwargs: Any) -> Any:
    return await db_func(None, *args, **kwargs)
