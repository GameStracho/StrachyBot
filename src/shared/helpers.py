from collections.abc import Awaitable, Callable
from typing import Concatenate, ParamSpec, TypeVar

import aiohttp
import discord
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import console

from .bot import StrachyBot

# Define a TypeVar bound to Pydantic's BaseModel
T = TypeVar("T", bound=BaseModel)


async def fetch_api(url: str, model_class: type[T]) -> T:
    """
    Fetches JSON data from a URL and parses it into the specified Pydantic model.
    """

    console.log_debug(f"Fetching '{url}' into '{model_class}'...")

    async with aiohttp.ClientSession() as session, session.get(url) as response:
        # Automatically raises an HTTPError for 4xx or 5xx responses
        response.raise_for_status()

        raw_json = await response.json()

        console.log_debug(f"Fetched '{url}'. Response received: \n\t{raw_json}")

        # Type-safe validation and parsing
        model: T = model_class.model_validate(raw_json)
        console.log_debug(f"Fetched '{url}' into \n\t{model}.")
        return model


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
