from typing import TypeVar

import aiohttp
from pydantic import BaseModel

import console

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
