from typing import List
import discord

from shared import console
from .button import TriviaButton

BUTTON_EMOJIS: List[str] = ["🇦", "🇧" , "🇨", "🇩"]

class TriviaView(discord.ui.View):
    __interaction: discord.Interaction

    def __init__(self, interaction: discord.Interaction, options: List[str], correct_answer: str, timeout: float = 180.0):
        super().__init__(timeout=timeout)

        for i, option in enumerate(options):
            print(i, option)
            is_correct: bool = (option == correct_answer)
            self.add_item(TriviaButton(label=option, is_correct=is_correct, emoji=BUTTON_EMOJIS[i]))

        self.__interaction = interaction

        console.log_debug(f"New TriviaView created: options = {options}, correct_answer = '{correct_answer}', timeout = {timeout} s.")


    async def on_timeout(self) -> None:
        # Disable all buttons and update the original message to reveal answers.
        for child in self.children:
            if isinstance(child, TriviaButton):
                child.disable()

        # Edit the original message to show disabled buttons
        await self.__interaction.response.edit_message(view=self)
