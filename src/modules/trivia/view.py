from typing import List
import discord

from shared import console
import modules.trivia.button as button

BUTTON_EMOJIS: List[str] = ["🇦", "🇧" , "🇨", "🇩"]

class TriviaView(discord.ui.View):
    __interaction: discord.Interaction

    def __init__(self, interaction: discord.Interaction, options: List[str], correct_answer: str, timeout: float = 180.0):
        super().__init__(timeout=timeout)

        for i, option in enumerate(options):
            print(i, option)
            is_correct: bool = (option == correct_answer)
            self.add_item(button.TriviaButton(label=option, is_correct=is_correct, emoji=BUTTON_EMOJIS[i], row=i))

        self.__interaction = interaction

        console.log_debug(f"New TriviaView created: options = {options}, correct_answer = '{correct_answer}', timeout = {timeout} s.")

    def disable_buttons(self):
        for child in self.children:
            if isinstance(child, button.TriviaButton):
                child.disable()


    async def on_timeout(self) -> None:
        self.disable_buttons()

        # Edit the original message to show disabled buttons
        await self.__interaction.response.edit_message(view=self)
