import discord
import time

TIMEOUT_COLOR: discord.Color = discord.Color.darker_grey()
DRAW_COLOR: discord.Color = discord.Color.light_grey()


def update_embed_field(embed: discord.Embed, name: str, value: str) -> None:
    for i, field in enumerate(embed.fields):
        if field.name == name:
            embed.set_field_at(index=i, name=name, value=value, inline=field.inline)
            return


def remove_embed_field(embed: discord.Embed, name: str) -> None:
    for i, field in enumerate(embed.fields):
        if field.name == name:
            embed.remove_field(index=i)
            return


def get_timeout_timestamp(view: discord.ui.View) -> str:
    if not view.timeout:
        return ""

    # Discord requires an integer Unix timestamp
    timestamp: int = int(time.time() + view.timeout)

    return f"<t:{timestamp}:R> ⏱️"
