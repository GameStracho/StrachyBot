import discord

from shared import console
import modules.trivia.view as view

class TriviaButton(discord.ui.Button):
    _is_correct: bool = False
    _game_id: int = -1

    def __init__(self, game_id: int, label: str, is_correct: bool, row: int, emoji: str = ""):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, emoji=emoji, row=row)

        self._is_correct = is_correct
        self._game_id = game_id

        console.log_debug((
            f"/trivia: New TriviaButton created for game {self._game_id}: "
            f"label = '{label}', is_correct = {is_correct}, emoji = '{emoji}', row = {row}."
        ))


    async def callback(self, interaction: discord.Interaction) -> None:
        parent_view: view.TriviaView | None = self.view
        assert parent_view is not None
        
        console.log_debug((
            f"/trivia: {"Correct" if self._is_correct else "Incorrect"} answer ({self.label}) "
            f"chosen for game {self._game_id} by user {interaction.user.display_name} ({interaction.user.id})."
        ))

        parent_view.disable_buttons()
        self.style = discord.ButtonStyle.primary

        # Edit the original message to show disabled buttons
        await interaction.response.edit_message(view=parent_view)


    def disable(self) -> None:
        """Disable the button and reveal whether the answer was correct or wrong."""
        self.disabled = True
        self.emoji = "✅" if self._is_correct else "❌"
