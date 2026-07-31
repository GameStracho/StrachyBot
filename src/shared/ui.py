import time

import discord

TIMEOUT_COLOR: discord.Color = discord.Color.darker_grey()
DRAW_COLOR: discord.Color = discord.Color.light_grey()

EMOJIS: dict[str, str] = {
    "a": "🇦",
    "b": "🇧",
    "c": "🇨",
    "d": "🇩",
    "e": "🇪",
    "f": "🇫",
    "g": "🇬",
    "h": "🇭",
    "i": "🇮",
    "j": "🇯",
    "k": "🇰",
    "l": "🇱",
    "m": "🇲",
    "n": "🇳",
    "o": "🇴",
    "p": "🇵",
    "q": "🇶",
    "r": "🇷",
    "s": "🇸",
    "t": "🇹",
    "u": "🇺",
    "v": "🇻",
    "w": "🇼",
    "x": "🇽",
    "y": "🇾",
    "z": "🇿",
    "0": "0️⃣",
    "1": "1️⃣",
    "2": "2️⃣",
    "3": "3️⃣",
    "4": "4️⃣",
    "5": "5️⃣",
    "6": "6️⃣",
    "7": "7️⃣",
    "8": "8️⃣",
    "9": "9️⃣"
}


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
