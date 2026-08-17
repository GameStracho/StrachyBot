from collections.abc import Awaitable, Callable

import discord

from shared import logger

from .constants import EMOJIS
from .helpers import get_timeout_timestamp, handle_error, load_attachment


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

        logger.debug(f"New ConfirmView created ({self.id}).")

    def build_embed(self, question: str) -> tuple[discord.Embed, discord.File]:
        logger.debug(f"Building embed for ConfirmView ({self.id}, question = '{question}')...")
        embed: discord.Embed = discord.Embed(
            color=discord.Color.blue(), title="Confirmation", description=question
        )

        icon, icon_url = load_attachment(
            path=__file__, filename="question.png", sub_dir="../images"
        )
        embed.set_thumbnail(url=icon_url)
        embed.add_field(name="Timeout", value=get_timeout_timestamp(self), inline=False)

        logger.debug(f"Embed build for ConfirmView ({self.id}).")
        return (embed, icon)

    async def on_timeout(self) -> None:
        logger.debug(f"ConfirmView ({self.id}) timed out.")

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
        await handle_error("shared", interaction=interaction, use_followup=False)

    @discord.ui.button()
    async def confirm_button(
        self, interaction: discord.Interaction, button: discord.ui.Button["ConfirmView"]
    ) -> None:
        logger.debug(f"ConfirmView ({self.id}) confirmed.")

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
        logger.debug(f"ConfirmView ({self.id}) cancelled.")

        self.stop()
        if self._on_cancel:
            await self._on_cancel(interaction)

        # Default cancel & cleanup behavior: delete the ephemeral confirmation prompt
        if not interaction.response.is_done():
            await interaction.response.defer()

        await interaction.delete_original_response()
