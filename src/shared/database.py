import os
from collections.abc import Awaitable, Callable
from typing import Concatenate, ParamSpec, TypeVar

import discord
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .bot import StrachyBot


def create_db_engine() -> AsyncEngine:
    """Creates asynchronous engine from the CONNECTION_STRING env variable."""
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    connection_string: str = os.getenv(
        "CONNECTION_STRING", "postgresql+asyncpg://localhost:Password1234@localhost:5432/StrachyBot"
    )

    # 'echo=True' logs all generated SQL to the console (great for debugging, turn off in prod)
    return create_async_engine(connection_string, echo=False, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Creates factory for database sessions from an engine."""
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


P = ParamSpec("P")  # parameter type
R = TypeVar("R")  # result value type


async def execute_db_operation(
    target: StrachyBot | discord.Interaction | discord.Message | discord.Client,
    db_func: Callable[Concatenate[AsyncSession, P], Awaitable[R]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> R | None:
    """
    Executes an async database operation with an AsyncSession.

    Automatically resolves the StrachyBot instance from target if given a
    discord.Interaction or discord.Message.

    :param target: StrachyBot instance, discord.Interaction, or discord.Message.
    :param db_func: Async function that takes `session: AsyncSession` as its first argument.
    :param args: Positional arguments passed to db_func after `session`.
    :param kwargs: Keyword arguments passed to db_func.
    :return: Result of db_func execution, or None if session factory is unavailable.
    """
    strachy_bot: StrachyBot | None = None

    if isinstance(target, StrachyBot):
        strachy_bot = target
    elif isinstance(target, discord.Interaction):
        if isinstance(target.client, StrachyBot):
            strachy_bot = target.client
    elif isinstance(target, discord.Message):
        client = target._state._get_client()
        if isinstance(client, StrachyBot):
            strachy_bot = client

    if not strachy_bot:
        return None

    session_factory = strachy_bot.get_db_session_factory()
    if not session_factory:
        return None

    async with session_factory() as session:
        if session:
            return await db_func(session, *args, **kwargs)

    return None
