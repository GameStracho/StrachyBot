import time
from datetime import date, datetime, timezone

import discord

WHITE_COLOR: discord.Color = discord.Color.from_rgb(255, 255, 255)
BROWN_COLOR: discord.Color = discord.Color.from_rgb(119, 56, 22)

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
    "9": "9️⃣",
    "game_draw": "🤝",
    "game_win": "🏆",
    "game_loss": "🥀",
    "game_turn": "⏳",
    "trivia_correct_answer": "✅",
    "trivia_wrong_answer": "❌",
    "trivia_correct_answer_selected": "✔️",
    "trivia_wrong_answer_selected": "✖️",
    "tic_empty_cell": "⬛",
    "wordle_guess_button": "✏️",
    "wordle_empty_letter": "⬜",
    "wordle_correct_letter": "🟩",
    "wordle_misplaced_letter": "🟨",
    "wordle_incorrect_letter": "⬛",
}

def _calculate_easter_sunday(year: int) -> date:
    """
    Calculates the month and day of Easter Sunday for a given year 
    using the Anonymous Gregorian Algorithm (Meeus/Jones/Butcher).
    Returns date of Easter Sunday.
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451

    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1

    return datetime(year, month, day, tzinfo=timezone.utc).date()


def get_player_colors(date: datetime | None = None) -> tuple[discord.Color, discord.Color]:
    """
        Returns player's and opponent's colors based on selected date.
    """
    if not date:
            date = datetime.now(timezone.utc)
    
    # New Year
    if (date.day == 1 and date.month == 1) or (date.day == 31 and date.month == 12):
        return (discord.Color.red(), discord.Color.blue())

    # Valentine's day
    if date.day == 14 and date.month == 2:
        return (discord.Color.purple(), discord.Color.orange())

    # April fools
    if date.day == 1 and date.month == 4:
        return (discord.Color.yellow(), WHITE_COLOR)

    # Easter
    if abs((date.date() - _calculate_easter_sunday(date.year)).days) <= 7:
        return (WHITE_COLOR, discord.Color.yellow())

    # Star Wars day
    if date.day == 4 and date.month == 5:
        return (discord.Color.blue(), discord.Color.red())

    # Summer (June, July, August)
    if date.month in (6, 7, 8):
        return (discord.Color.yellow(), discord.Color.blue())
        
    # Halloween (October)
    if date.month == 10:
        return (discord.Color.orange(), BROWN_COLOR)

    # Christmas Season (December)
    if date.month == 12:
        return (discord.Color.red(), discord.Color.green())

    # Default
    return (discord.Color.purple(), discord.Color.orange())


def get_player_emojis(date: datetime | None = None) -> tuple[str, str]:
    """
    Returns player's and opponent's emojis based on selected date.
    """
    if not date:
        date = datetime.now(timezone.utc)

    # New Year
    if (date.day == 1 and date.month == 1) or (date.day == 31 and date.month == 12):
        return ("🎉", "🎆")

    # Valentine's day
    if date.day == 14 and date.month == 2:
        return ("💜", "🧡")

    # April fools
    if date.day == 1 and date.month == 4:
        return ("🤪", "🤡")

    # Easter
    if abs((date.date() - _calculate_easter_sunday(date.year)).days) <= 7:
        return ("🐰", "🐣")

    # Star Wars day
    if date.day == 4 and date.month == 5:
        return ("🩵", "❤️")

    # Summer (June, July, August)
    if date.month in (6, 7, 8):
        return ("☀️", "🌊")
        
    # Halloween (October)
    if date.month == 10:
        return ("👻", "🦉")

    # Christmas Season (December)
    if date.month == 12:
        return ("🎁", "🎄")

    # Default
    return ("🟣", "🟠")


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
