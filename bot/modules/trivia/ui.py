import random

import discord
import httpx
from typing_extensions import override

from shared import logger, models, types, ui
from shared.modules.trivia import ETriviaCategory, ETriviaDifficulty, TriviaResponse


class TriviaView(discord.ui.View):
    _match_id: int
    _player_id: int
    _status: models.EMatchStatus
    _question: str
    _category: ETriviaCategory
    _difficulty: ETriviaDifficulty
    _api_client: httpx.AsyncClient
    message: discord.Message

    def __init__(
        self,
        game_data: TriviaResponse,
        api_client: httpx.AsyncClient,
        timeout: float = 60.0,
    ) -> None:
        super().__init__(timeout=timeout)

        self._match_id = game_data.match_id
        self._player_id = game_data.player_id
        self._status = game_data.status
        self._question = game_data.question
        self._category = game_data.category
        self._difficulty = game_data.difficulty
        self._api_client = api_client

        options: list[tuple[str, bool]] = [(game_data.correct_answer, True)]
        for incorrect in game_data.incorrect_answers:
            options.append((incorrect, False))
        random.shuffle(options)

        for i, (label, is_correct) in enumerate(options):
            self.add_item(
                TriviaButton(
                    parent_view=self,
                    label=label,
                    is_correct=is_correct,
                    emoji=ui.EMOJIS[chr(ord("a") + i)],
                    row=i,
                )
            )

        logger.debug(f"New TriviaView created for game {self._match_id} with {timeout}s timeout.")

    @property
    def match_id(self) -> int:
        return self._match_id

    @property
    def status(self) -> models.EMatchStatus:
        return self._status

    def build_embed(self, player: types.User) -> tuple[discord.Embed, discord.File]:
        embed: discord.Embed = discord.Embed(title="Trivia", color=discord.Color.dark_gold())
        embed.set_author(name=player.display_name, icon_url=player.display_avatar)

        embed.add_field(name="Category", value=self._category, inline=True)
        embed.add_field(name="Difficulty", value=self._difficulty, inline=True)
        embed.add_field(name="Question", value=self._question, inline=False)
        embed.add_field(name="Timeout", value=ui.get_timeout_timestamp(view=self), inline=False)

        icon, icon_url = ui.load_attachment(path=__file__, filename="icon.png")
        embed.set_thumbnail(url=icon_url)

        return (embed, icon)

    def update_embed(self, embed: discord.Embed) -> None:
        match self._status:
            case models.EMatchStatus.WIN:
                embed.color = discord.Color.green()
            case models.EMatchStatus.LOSS:
                embed.color = discord.Color.red()
            case models.EMatchStatus.TIMEOUT:
                embed.color = ui.COLORS["game_timeout"]
            case _:
                raise ValueError(self._status)

        self.disable_buttons()
        self.stop()
        ui.embed.remove_field(embed=embed, name="Timeout")

    def disable_buttons(self) -> None:
        logger.debug(f"Revealing answers for game {self._match_id}...")
        for child in self.children:
            if isinstance(child, TriviaButton):
                child.disable()
        logger.debug(f"Answers revealed for game {self._match_id}.")

    @override
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            if interaction.user.id != self._player_id:
                logger.warning(
                    f"Ineligible user {interaction.user.display_name} "
                    f"({interaction.user.id}) "
                    f"responded to game {self._match_id}."
                )

                embed, icon = ui.embed.build_warning(message="You cannot respond to this game.")
                await interaction.response.send_message(embed=embed, file=icon, ephemeral=True)
                return False  # Aborts processing and DOES NOT reset/extend the view timeout

            return True  # Authorized click; allow execution
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
            return False

    @override
    async def on_timeout(self) -> None:
        if self._status != models.EMatchStatus.PENDING:
            return

        response = await self._api_client.patch(url=f"{self._match_id}/timeout")
        response.raise_for_status()

        self._status = models.EMatchStatus.TIMEOUT
        embed: discord.Embed = ui.embed.extract(target=self.message, index=0, hide_icon=True)
        self.update_embed(embed=embed)
        await self.message.edit(embed=embed, view=self)


class TriviaButton(discord.ui.Button["TriviaView"]):
    _parent_view: TriviaView
    _is_correct: bool
    _is_selected: bool
    _full_answer: str

    def __init__(
        self,
        parent_view: TriviaView,
        label: str,
        is_correct: bool,
        row: int,
        emoji: str = "",
    ) -> None:
        display_label = label[:77] + "..." if len(label) > 80 else label
        super().__init__(
            label=display_label, style=discord.ButtonStyle.secondary, emoji=emoji, row=row
        )

        self._parent_view = parent_view
        self._is_correct = is_correct
        self._is_selected = False
        self._full_answer = label

        logger.debug(
            f"New TriviaButton created for game {parent_view.match_id}: "
            f"label = '{display_label}', is_correct = {is_correct}, emoji = '{emoji}', row = {row}."
        )

    @override
    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            response = await self._parent_view._api_client.patch(
                url=f"{self._parent_view.match_id}/answer",
                params={"answer": self._full_answer},
            )
            response.raise_for_status()
            game_data: TriviaResponse = TriviaResponse.model_validate(response.json())

            self._is_selected = True
            self._parent_view._status = game_data.status

            embed: discord.Embed = ui.embed.extract(target=interaction, index=0, hide_icon=True)
            self._parent_view.update_embed(embed=embed)

            # Edit the original message to show disabled buttons
            await interaction.response.edit_message(embed=embed, view=self._parent_view)
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)

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
