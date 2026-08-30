from typing import Any, TypeVar

import aiohttp
import requests
from pydantic import BaseModel

from .logs import logger

# Define a TypeVar bound to Pydantic's BaseModel
T = TypeVar("T", bound=BaseModel)


async def fetch_model(url: str, model_class: type[T]) -> T:
    """
    Fetches JSON data from a URL and parses it into the specified Pydantic model.
    """

    logger.debug(f"Fetching '{url}' into '{model_class}'...")

    async with aiohttp.ClientSession() as session, session.get(url) as response:
        # Automatically raises an HTTPError for 4xx or 5xx responses
        response.raise_for_status()

        raw_json = await response.json()

        logger.debug(f"Fetched '{url}'. Response received: \n{raw_json}")

        # Type-safe validation and parsing
        model: T = model_class.model_validate(raw_json)
        logger.debug(f"Fetched '{url}' into \n{model}.")
        return model


async def fetch_raw(url: str) -> bytes:
    """
    Fetches raw JSON data from a URL.
    """

    logger.debug(f"Fetching '{url}'...")

    response: requests.Response = requests.get(url=url)

    logger.debug(f"Fetched '{url}'. Response received: \n{response}")
    return response.content


async def fetch_json(url: str) -> Any:
    """
    Fetches raw JSON data from a URL.
    """

    logger.debug(f"Fetching '{url}'...")

    async with aiohttp.ClientSession() as session, session.get(url) as response:
        # Automatically raises an HTTPError for 4xx or 5xx responses
        response.raise_for_status()

        raw_json = await response.json()
        logger.debug(f"Fetched '{url}'. Response received: \n{raw_json}")

        return raw_json
