from typing import List, Tuple
import discord
import random

from shared import console, messages, models, bot, ui
from .game import TriviaGame
from .repository import update_match

BUTTON_EMOJIS: List[str] = ["🇦", "🇧" , "🇨", "🇩"]

class TriviaView(discord.ui.View):
    _game: TriviaGame
    message: discord.Message | None

    def __init__(self, game: TriviaGame, timeout: float = 10.0):
        super().__init__(timeout=timeout)

        self._game = game

        options: List[Tuple[str, bool]] = [(self._game.get_correct_answer(), True)]

        for incorrect_answer in self._game.get_incorrect_answers():
            options.append((incorrect_answer, False))

        random.shuffle(options)

        for i, option in enumerate(options):
            label, is_correct = option
            self.add_item(TriviaButton(game_id=self._game.match_id, label=label, is_correct=is_correct, emoji=BUTTON_EMOJIS[i], row=i))

        console.log_debug(f"/trivia: New TriviaView created for game {self._game.match_id} with {timeout}s timeout.")


    def get_game(self) -> TriviaGame:
        return self._game


    def disable_buttons(self) -> None:
        self._game.end()

        console.log_debug(f"/trivia: Revealing answers for game {self._game.match_id}...")
        for child in self.children:
            if isinstance(child, TriviaButton):
                child.disable()
        console.log_debug(f"/trivia: Answers revealed for game {self._game.match_id}.")


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
            try:
                if interaction.user.id != self._game.get_player_id():
                    console.log_warning((
                        f"/trivia: Ineligible user {interaction.user.display_name} ({interaction.user.id}) "
                        f"responded to game {self._game.match_id}"
                    ))
                    await interaction.response.send_message("You cannot respond to this game.", ephemeral=True)
                    return False  # Aborts processing and DOES NOT reset/extend the view timeout
    
                return True  # Authorized click; allow execution
            except Exception:
                await messages.handle_error(command="/trivia", interaction=interaction, use_followup=False)
                return False


    async def on_timeout(self) -> None:
        if self._game.is_over() or self.message is None:
            return

        console.log_info(f"/trivia: Game {self._game.match_id} timed out.")
        self.disable_buttons()

        embed: discord.Embed = self.message.embeds[0]
        embed.color = ui.TIMEOUT_COLOR
        ui.remove_embed_field(embed=embed, name="Timeout")

        # hide a second icon appearing above the embed
        embed.set_thumbnail(url="attachment://icon.png")

        strachy_bot = self.message._state._get_client()
        assert isinstance(strachy_bot, bot.StrachyBot)

        session_factory = strachy_bot.get_db_session_factory()

        if session_factory:
            async with session_factory() as session:
                if session:
                    await update_match(session=session, match_id=self._game.match_id, status=models.EMatchStatus.TIMEOUT)

        # Edit the original message to show disabled buttons
        await self.message.edit(embed=embed, view=self)


class TriviaButton(discord.ui.Button["TriviaView"]):
    _is_correct: bool

    def __init__(
            self, game_id: int, label: str, is_correct: bool, row: int, emoji: str = ""):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, emoji=emoji, row=row)

        self._is_correct = is_correct

        console.log_debug((
            f"/trivia: New TriviaButton created for game {game_id}: "
            f"label = '{label}', is_correct = {is_correct}, emoji = '{emoji}', row = {row}."
        ))


    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            parent_view = self.view
            assert isinstance(parent_view, TriviaView)
            
            answer_type: str = "Correct" if self._is_correct else "Incorrect"

            console.log_info((
                f"/trivia: {answer_type} answer ({self.label}) "
                f"chosen for game {parent_view.get_game().match_id} by user {interaction.user.display_name} ({interaction.user.id})."
            ))

            message: discord.Message | None = interaction.message
            assert message is not None

            embed: discord.Embed = message.embeds[0]
            ui.remove_embed_field(embed=embed, name="Timeout")

            # hide a second icon appearing above the embed
            embed.set_thumbnail(url="attachment://icon.png")

            parent_view.disable_buttons()

            status: models.EMatchStatus = models.EMatchStatus.PENDING

            if self._is_correct:
                embed.color = discord.Color.green()
                self.style = discord.ButtonStyle.green
                self.emoji = "✔️"
                status = models.EMatchStatus.WIN
            else:
                embed.color = discord.Color.red()
                self.style = discord.ButtonStyle.red
                self.emoji = "✖️"
                status = models.EMatchStatus.LOSS

            strachy_bot = interaction.client
            assert isinstance(strachy_bot, bot.StrachyBot)

            session_factory = strachy_bot.get_db_session_factory()

            if session_factory:
                async with session_factory() as session:
                    await update_match(session=session, match_id=parent_view.get_game().match_id, status=status)

            # Edit the original message to show disabled buttons
            await interaction.response.edit_message(embed=embed, view=parent_view)
        except Exception:
            await messages.handle_error(command="/trivia", interaction=interaction, use_followup=False)


    def disable(self) -> None:
        """Disable the button and reveal whether the answer was correct or wrong."""
        self.disabled = True
        self.emoji = "✅" if self._is_correct else "❌"
