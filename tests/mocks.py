from __future__ import annotations 

from typing import Any, List, Dict, Tuple
from types import SimpleNamespace
from unittest.mock import AsyncMock
import discord

from shared import models, bot

class DummyStrachyBot(bot.StrachyBot):
    pass

class DummyConnection():
    async def run_sync(self, fn: Any, *arg: Any, **kw: Any) -> Any:
        return None


class DummyTransaction():
    async def __aenter__(self) -> DummyConnection:
        return DummyConnection()


    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False


class DummyContextManager():
    def __init__(self, session: DummySession) -> None:
        self.session = session


    async def __aenter__(self) -> DummySession:
        return self.session


    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False


class DummyResult():
    def __init__(self, value: Any) -> None:
        self._value = value


    def scalar_one_or_none(self) -> Any:
        return self._value


class DummySession():
    def __init__(self, match: models.Match | None = None) -> None:
        self.match = match
        self.added: List[Any] = []
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


    async def execute(self, *args: Any, **kwargs: Any) -> DummyResult:
        self.executed = True
        return DummyResult(self.match)


class DummyResponse():
    def __init__(self) -> None:
        self.edit_calls: List[Dict[str, Any]] = []
        self.send_calls: List[Tuple[Any, Dict[str, Any]]] = []
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

    def __init__(self, user_id: int = 1, username: str = "Tester") -> None:
        # Avoid running full discord.Interaction internal state machine logic during raw unit tests
        self.user = SimpleNamespace(id=user_id, display_name=username)
        self.response = SimpleNamespace(defer=AsyncMock(), send_message=AsyncMock(), edit_message=AsyncMock())
        self.followup = SimpleNamespace(send=AsyncMock())
        self.original_response_message = None
        self._followup_sent: Dict[str, Any] | None = None


    @property
    def client(self) -> Any:
        return DummyStrachyBot()


    async def defer(self, *, ephemeral: bool = False, thinking: bool = False) -> None:
        await self.response.defer()


    async def followup_send(self, **kwargs: Any) -> None:
        self._followup_sent = kwargs


    async def original_response(self) -> Any:
        return self.original_response_message
