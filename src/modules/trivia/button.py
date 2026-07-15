import discord

from shared import console
import modules.trivia.view as view

class TriviaButton(discord.ui.Button):
    _is_correct: bool = False

    def __init__(self, label: str, is_correct: bool, row: int, emoji: str = ""):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, emoji=emoji, row=row)

        self._is_correct = is_correct
        console.log_debug(f"New TriviaButton created: label = '{label}', is_correct = {is_correct}, emoji = '{emoji}', row = {row}.")


    async def callback(self, interaction: discord.Interaction) -> None:
        parent_view: view.TriviaView = self.view
        if parent_view is None:
            return

        parent_view.disable_buttons()

        # Edit the original message to show disabled buttons
        await interaction.response.edit_message(view=parent_view)


    def disable(self) -> None:
        """Disable the button and reveal whether the answer was correct or wrong."""
        self.disabled = True
        self.emoji = "✅" if self._is_correct else "❌"
