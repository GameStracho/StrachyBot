from typing import Tuple, Type, TypeVar
import re
import discord
import aiohttp
from pydantic import BaseModel

import shared.console as console

def load_attachment(path: str, filename: str) -> Tuple[discord.File, str]:
    """
        Loads attachment 'filename' from 'path'.

        Returns loaded the attachment and its url.
    """
    
    attachment_path: str = re.sub(pattern="[^\/]*$", repl="", string=path) + filename
    attachment: discord.File = discord.File(fp=attachment_path, filename=filename)

    console.log_debug(f"Attachment '{attachment_path}' loaded.")

    return (attachment, f"attachment://{filename}")

# Define a TypeVar bound to Pydantic's BaseModel
T = TypeVar("T", bound=BaseModel)

async def fetch_api(url: str, model_class: Type[T]) -> T:
    """
    Fetches JSON data from a URL and parses it into the specified Pydantic model.
    """

    console.log_debug(f"Fetching '{url}' into '{model_class}'...")

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            # Automatically raises an HTTPError for 4xx or 5xx responses
            response.raise_for_status() 
            
            raw_json = await response.json()

            console.log_debug(f"Fetched '{url}'. Response received: \n\t{raw_json}")
            
            # Type-safe validation and parsing
            model: T = model_class.model_validate(raw_json)
            console.log_debug(f"Fetched '{url}' into \n\t{model}.")
            return model
