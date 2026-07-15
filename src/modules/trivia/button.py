import discord

from shared import console

class TriviaButton(discord.ui.Button):
    _is_correct: bool = False

    def __init__(self, label: str, is_correct: bool = False, emoji: str = ""):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, emoji=emoji)

        self._is_correct = is_correct
        console.log_debug(f"New TriviaButton created: label = '{label}', is_correct = {is_correct}, emoji = '{emoji}'.")


    async def callback(self, interaction: discord.Interaction) -> None:
        # Disable all buttons and update the original message to reveal answers.
        view = self.view
        if view is None:
            return

        for child in view.children:
            if isinstance(child, TriviaButton):
                child.disable()

        # Edit the original message to show disabled buttons
        await interaction.response.edit_message(view=view)


    def disable(self) -> None:
        """Disable the button and reveal whether the answer was correct or wrong."""
        self.disabled = True
        self.emoji = "✅" if self._is_correct else "❌"
