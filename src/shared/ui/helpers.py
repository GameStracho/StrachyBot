import re
import time
import traceback

import discord

import console


def get_timeout_timestamp(view: discord.ui.View) -> str:
    if not view.timeout:
        return ""

    # Discord requires an integer Unix timestamp
    timestamp: int = int(time.time() + view.timeout)

    return f"<t:{timestamp}:R> ⏱️"


async def handle_error(
    command: str, interaction: discord.Interaction, use_followup: bool = False
) -> None:
    """
    Print error message with details to console and send generic message to user.
    IMPORTANT: only call from an except block!
    """
    console.log_error(
        f"{command}: An unexpected error occurred for {interaction.user.display_name}: "
        f"\n{traceback.format_exc()}"
    )

    embed: discord.Embed = discord.Embed(color=discord.Color.red())
    embed.title = "Error"
    embed.description = "An unexpected error occurred. Try again later."

    icon: discord.File = discord.File("./src/images/error.png", filename="error.png")
    embed.set_thumbnail(url="attachment://error.png")

    if use_followup:
        await interaction.followup.send(embed=embed, file=icon, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, file=icon, ephemeral=True)


def load_attachment(path: str, filename: str, sub_dir: str = "") -> tuple[discord.File, str]:
    """
    Loads attachment 'filename' from 'path/sub_dir/filename'.

    Returns loaded the attachment and its url.
    """

    attachment_path: str = (
        re.sub(pattern=r"[^\/]*$", repl="", string=path) + f"/{sub_dir}/{filename}"
    )
    attachment: discord.File = discord.File(fp=attachment_path, filename=filename)

    console.log_debug(f"Attachment '{attachment_path}' loaded.")

    return (attachment, f"attachment://{filename}")
