import re
import time
import traceback
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime

import discord

import console
from shared import ui

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
    "game_timeout": "⏰",
    "game_surrender": "🏳️",
    "trivia_correct_answer": "✅",
    "trivia_wrong_answer": "❌",
    "trivia_correct_answer_selected": "✔️",
    "trivia_wrong_answer_selected": "✖️",
    "tic_empty_cell": "⬛",
    "wordle_enter_guess_button": "✏️",
    "wordle_random_guess_button": "🎲",
    "wordle_unused_letter": "⬜",
    "wordle_correct_letter": "🟩",
    "wordle_misplaced_letter": "🟨",
    "wordle_incorrect_letter": "⬛",
    "confirm_button": "✔️",
    "cancel_button": "✖️",
}


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
    ) % 3

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


def extract_embed(interaction: discord.Interaction, index: int, hide_icon: bool) -> discord.Embed:
    message: discord.Message | None = interaction.message
    assert message is not None

    return extract_embed_from_message(message=message, index=index, hide_icon=hide_icon)


def extract_embed_from_message(
    message: discord.Message, index: int, hide_icon: bool
) -> discord.Embed:
    embed: discord.Embed = message.embeds[index]

    if hide_icon:
        # hide a second icon appearing above the embed
        embed.set_thumbnail(url="attachment://icon.png")

    return embed


class ConfirmView(discord.ui.View):
    _on_confirm: Callable[[discord.Interaction], Awaitable[None]]
    _on_cancel: Callable[[discord.Interaction], Awaitable[None]] | None = None
    _interaction: discord.Interaction | None

    """
    A generic, reusable confirmation View.

    :param on_confirm: Async function executed when the confirm button is clicked.
    :param on_cancel: Optional async function executed when the cancel button is clicked.
    :param confirm_label: Text label for the confirm button.
    :param cancel_label: Text label for the cancel button.
    :param confirm_style: discord.ButtonStyle for the confirm button.
    :param cancel_style: discord.ButtonStyle for the cancel button.
    :param confirm_emoji: Optional emoji for the confirm button.
    :param cancel_emoji: Optional emoji for the cancel button.
    :param timeout: Time in seconds before the confirmation prompt expires.
    """

    def __init__(
        self,
        on_confirm: Callable[[discord.Interaction], Awaitable[None]],
        on_cancel: Callable[[discord.Interaction], Awaitable[None]] | None = None,
        interaction: discord.Interaction | None = None,
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
        confirm_style: discord.ButtonStyle = discord.ButtonStyle.green,
        cancel_style: discord.ButtonStyle = discord.ButtonStyle.red,
        confirm_emoji: str | None = EMOJIS["confirm_button"],
        cancel_emoji: str | None = EMOJIS["cancel_button"],
        timeout: float = 30.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
        self._interaction = interaction

        # Dynamically set button properties
        self.confirm_button.label = confirm_label
        self.confirm_button.style = confirm_style
        if confirm_emoji:
            self.confirm_button.emoji = confirm_emoji

        self.cancel_button.label = cancel_label
        self.cancel_button.style = cancel_style
        if cancel_emoji:
            self.cancel_button.emoji = cancel_emoji

        console.log_debug(f"New ConfirmView created ({self.id}).")

    def build_embed(self, question: str) -> tuple[discord.Embed, discord.File]:
        console.log_debug(f"Building embed for ConfirmView ({self.id}, question = '{question}')...")
        embed: discord.Embed = discord.Embed(
            color=discord.Color.blue(), title="Confirmation", description=question
        )

        icon, icon_url = ui.load_attachment(
            path=__file__, filename="question.png", sub_dir="images"
        )
        embed.set_thumbnail(url=icon_url)
        embed.add_field(name="Timeout", value=get_timeout_timestamp(self), inline=False)

        console.log_debug(f"Embed build for ConfirmView ({self.id}).")
        return (embed, icon)

    async def on_timeout(self) -> None:
        console.log_debug(f"ConfirmView ({self.id}) timed out.")

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        if self._interaction:
            await self._interaction.delete_original_response()

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item["ConfirmView"],
    ) -> None:
        await ui.handle_error("shared", interaction=interaction, use_followup=False)

    @discord.ui.button()
    async def confirm_button(
        self, interaction: discord.Interaction, button: discord.ui.Button["ConfirmView"]
    ) -> None:
        console.log_debug(f"ConfirmView ({self.id}) confirmed.")

        self.stop()
        await self._on_confirm(interaction)

        # Delete the ephemeral confirmation message after execution
        if not interaction.response.is_done():
            await interaction.response.defer()

        await interaction.delete_original_response()

    @discord.ui.button()
    async def cancel_button(
        self, interaction: discord.Interaction, button: discord.ui.Button["ConfirmView"]
    ) -> None:
        console.log_debug(f"ConfirmView ({self.id}) cancelled.")

        self.stop()
        if self._on_cancel:
            await self._on_cancel(interaction)

        # Default cancel & cleanup behavior: delete the ephemeral confirmation prompt
        if not interaction.response.is_done():
            await interaction.response.defer()

        await interaction.delete_original_response()
