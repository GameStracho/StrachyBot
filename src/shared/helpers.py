from typing import Tuple
import re
import discord

from .console import log_debug

def load_attachment(path: str, filename: str) -> Tuple[discord.File, str]:
    """
        Loads attachment 'filename' from 'path'.

        Returns loaded the attachment and its url.
    """
    
    attachment_path: str = re.sub(pattern="[^\/]*$", repl="", string=path) + filename
    attachment: discord.File = discord.File(fp=attachment_path, filename=filename)

    log_debug(f"Attachment '{attachment_path}' loaded.")

    return (attachment, f"attachment://{filename}")