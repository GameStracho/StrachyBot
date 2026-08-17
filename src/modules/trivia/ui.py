import random
from typing import override

import discord

from shared import logger, models, types, ui

from .game import TriviaGame


class TriviaView(discord.ui.View):
    _game: TriviaGame
    message: discord.Message | None

    def __init__(self, game: TriviaGame, timeout: float = 10.0):
        super().__init__(timeout=timeout)

        self._game = game

        options: list[tuple[str, bool]] = [(self._game.correct_answer, True)]

        for incorrect_answer in self._game.incorrect_answers:
            options.append((incorrect_answer, False))

        random.shuffle(options)

        for i, option in enumerate(options):
            label, is_correct = option
            self.add_item(
                TriviaButton(
                    parent_view=self,
                    label=label,
                    is_correct=is_correct,
                    emoji=ui.EMOJIS[chr(ord("a") + i)],
                    row=i,
                )
            )

        logger.debug(
            f"/trivia: New TriviaView created for game {self._game.match_id} "
            f"with {timeout}s timeout."
        )

    @property
    def game(self) -> TriviaGame:
        return self._game

    def build_embed(self) -> tuple[discord.Embed, discord.File]:
        user: types.User = self._game.player

        embed: discord.Embed = discord.Embed(title="Trivia", color=discord.Color.dark_gold())
        embed.set_author(name=user.display_name, icon_url=user.display_avatar)

        embed.add_field(name="Category", value=self._game.category, inline=True)
        embed.add_field(name="Difficulty", value=self._game.difficulty, inline=True)
        embed.add_field(name="Question", value=self._game.question, inline=False)
        embed.add_field(name="Timeout", value=ui.get_timeout_timestamp(view=self), inline=False)

        icon, icon_url = ui.load_attachment(path=__file__, filename="icon.png")
        embed.set_thumbnail(url=icon_url)

        return (embed, icon)

    def update_embed(self, embed: discord.Embed) -> None:
        match self._game.status:
            case models.EMatchStatus.WIN:
                embed.color = discord.Color.green()
            case models.EMatchStatus.LOSS:
                embed.color = discord.Color.red()
            case _:
                raise ValueError(self._game.status)

        self.disable_buttons()
        self.stop()
        ui.embed.remove_field(embed=embed, name="Timeout")

    def disable_buttons(self) -> None:
        logger.debug(f"/trivia: Revealing answers for game {self._game.match_id}...")
        for child in self.children:
            if isinstance(child, TriviaButton):
                child.disable()
        logger.debug(f"/trivia: Answers revealed for game {self._game.match_id}.")

    @override
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            if interaction.user.id != self._game.player.id:
                logger.warning(
                    f"/trivia: Ineligible user {interaction.user.display_name} "
                    f"({interaction.user.id}) "
                    f"responded to game {self._game.match_id}"
                )

                embed, icon = ui.embed.build_warning(message="You cannot respond to this game.")

                await interaction.response.send_message(embed=embed, file=icon, ephemeral=True)
                return False  # Aborts processing and DOES NOT reset/extend the view timeout

            return True  # Authorized click; allow execution
        except Exception:
            await ui.handle_error(command="/trivia", interaction=interaction, use_followup=False)
            return False

    @override
    async def on_timeout(self) -> None:
        if self._game.status != models.EMatchStatus.PENDING or self.message is None:
            return

        self.disable_buttons()
        await self._game.handle_timeout()

        embed: discord.Embed = ui.embed.extract(target=self.message, index=0, hide_icon=True)
        embed.color = ui.COLORS["game_timeout"]
        ui.embed.remove_field(embed=embed, name="Timeout")

        # Edit the original message to show disabled buttons
        await self.message.edit(embed=embed, view=self)


class TriviaButton(discord.ui.Button[TriviaView]):
    _parent_view: TriviaView
    _is_correct: bool
    _is_selected: bool
    _full_answer: str

    def __init__(
        self, parent_view: TriviaView, label: str, is_correct: bool, row: int, emoji: str = ""
    ):
        display_label = label[:77] + "..." if len(label) > 80 else label
        super().__init__(
            label=display_label, style=discord.ButtonStyle.secondary, emoji=emoji, row=row
        )

        self._parent_view = parent_view
        self._is_correct = is_correct
        self._is_selected = False
        self._full_answer = label

        logger.debug(
            f"/trivia: New TriviaButton created for game {parent_view.game.match_id}: "
            f"label = '{display_label}', is_correct = {is_correct}, emoji = '{emoji}', row = {row}."
        )

    @override
    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            answer: str = self._full_answer
            await self._parent_view.game.select_answer(answer=answer)

            self._is_selected = True
            embed: discord.Embed = ui.embed.extract(target=interaction, index=0, hide_icon=True)
            self._parent_view.update_embed(embed=embed)

            # Edit the original message to show disabled buttons
            await interaction.response.edit_message(embed=embed, view=self._parent_view)
        except Exception:
            await ui.handle_error(command="/trivia", interaction=interaction, use_followup=False)

    def disable(self) -> None:
        """Disable the button and reveal whether the answer was correct or wrong."""
        self.disabled = True

        match (self._is_selected, self._is_correct):
            case (True, True):
                self.style = discord.ButtonStyle.green
                self.emoji = ui.EMOJIS["trivia_correct_answer_selected"]
            case (True, False):
                self.style = discord.ButtonStyle.red
                self.emoji = ui.EMOJIS["trivia_wrong_answer_selected"]
            case (False, True):
                self.emoji = ui.EMOJIS["trivia_correct_answer"]
            case (False, False):
                self.emoji = ui.EMOJIS["trivia_wrong_answer"]
