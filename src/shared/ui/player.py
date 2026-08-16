from datetime import UTC, date, datetime

import discord

from .constants import COLORS


def _calculate_easter_sunday(year: int) -> date:
    """
    Calculates the month and day of Easter Sunday for a given year
    using the Anonymous Gregorian Algorithm (Meeus/Jones/Butcher).
    Returns date of Easter Sunday.
    """
    # 1. Break down the year
    metonic_cycle_pos = year % 19
    century = year // 100
    year_in_century = year % 100

    # 2. Compute calendar shifts and corrections
    leap_centuries = century // 4
    century_remainder = century % 4
    lunar_epact_correction = (century + 8) // 25
    solar_leap_correction = (century - lunar_epact_correction + 1) // 3

    # 3. Find the Paschal Full Moon (Days past March 21)
    # The '15' represents the base alignment for the Gregorian reform
    lunar_epact = (
        19 * metonic_cycle_pos + century - leap_centuries - solar_leap_correction + 15
    ) % 30

    # 4. Determine day of the week adjustments
    leap_years_in_century = year_in_century // 4
    year_remainder = year_in_century % 4
    sunday_correction = (
        32 + 2 * century_remainder + 2 * leap_years_in_century - lunar_epact - year_remainder
    ) % 7

    # 5. Handle rare Metonic calendar exceptions
    metonic_exception = (metonic_cycle_pos + 11 * lunar_epact + 22 * sunday_correction) // 451

    # 6. Extract final Month and Day
    # The '114' acts as a mathematical offset to scale the results into March/April
    total_days_offset = lunar_epact + sunday_correction - 7 * metonic_exception + 114

    month = total_days_offset // 31  # 3 = March, 4 = April
    day = (total_days_offset % 31) + 1

    return datetime(year, month, day, tzinfo=UTC).date()


def get_player_colors(date: datetime | None = None) -> tuple[discord.Color, discord.Color]:
    """
    Returns player's and opponent's colors based on selected date.
    """
    return (discord.Color.purple(), discord.Color.orange())

    if not date:
        date = datetime.now(UTC)

    # New Year
    if (date.day == 1 and date.month == 1) or (date.day == 31 and date.month == 12):
        return (discord.Color.red(), discord.Color.blue())

    # Valentine's day
    if date.day == 14 and date.month == 2:
        return (discord.Color.purple(), discord.Color.orange())

    # April fools
    if date.day == 1 and date.month == 4:
        return (discord.Color.yellow(), COLORS["white"])

    # Easter
    if abs((date.date() - _calculate_easter_sunday(date.year)).days) <= 7:
        return (COLORS["white"], discord.Color.yellow())

    # Star Wars day
    if date.day == 4 and date.month == 5:
        return (discord.Color.blue(), discord.Color.red())

    # Summer (June, July, August)
    if date.month in (6, 7, 8):
        return (discord.Color.yellow(), discord.Color.blue())

    # Halloween (October)
    if date.month == 10:
        return (discord.Color.orange(), COLORS["brown"])

    # Christmas Season (December)
    if date.month == 12:
        return (discord.Color.red(), discord.Color.green())

    # Default
    return (discord.Color.purple(), discord.Color.orange())


def get_player_emojis(date: datetime | None = None) -> tuple[str, str]:
    """
    Returns player's and opponent's emojis based on selected date.
    """
    return ("🟣", "🟠")

    if not date:
        date = datetime.now(UTC)

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
