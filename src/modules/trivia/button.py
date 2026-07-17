import discord

from shared import console, messages, models, bot
import modules.trivia.view as view
from .repository import update_match

class TriviaButton(discord.ui.Button["view.TriviaView"]):
    _is_correct: bool
    _game_id: int
    _player_id: int

    def __init__(
            self, game_id: int, player_id: int,
            label: str, is_correct: bool, row: int, emoji: str = ""):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, emoji=emoji, row=row)

        self._game_id = game_id
        self._player_id = player_id
        self._is_correct = is_correct

        console.log_debug((
            f"/trivia: New TriviaButton created for game {self._game_id}: "
            f"label = '{label}', is_correct = {is_correct}, emoji = '{emoji}', row = {row}."
        ))


    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            if interaction.user.id != self._player_id:
                console.log_warning((
                    f"/trivia: Ineligible user {interaction.user.display_name} ({interaction.user.id}) "
                    f"responded to game {self._game_id} started by player {self._player_id}"
                ))
                await interaction.response.send_message("You cannot respond to this game.", ephemeral=True)
                return
            
            parent_view = self.view
            assert isinstance(parent_view, view.TriviaView)
            
            answer_type: str = "Correct" if self._is_correct else "Incorrect"

            console.log_debug((
                f"/trivia: {answer_type} answer ({self.label}) "
                f"chosen for game {self._game_id} by user {interaction.user.display_name} ({interaction.user.id})."
            ))

            message: discord.Message | None = interaction.message
            assert message is not None

            embed: discord.Embed = message.embeds[0]
            embed.description = "" # remove timeout countdown

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

            async with strachy_bot.db_session_factory() as session:
                await update_match(session=session, match_id=self._game_id, status=status)

            # Edit the original message to show disabled buttons
            await interaction.response.edit_message(embed=embed, view=parent_view)
        except Exception:
            await messages.handle_error(command="/trivia", interaction=interaction, use_followup=False)


    def disable(self) -> None:
        """Disable the button and reveal whether the answer was correct or wrong."""
        self.disabled = True
        self.emoji = "✅" if self._is_correct else "❌"
