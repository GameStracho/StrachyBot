from typing import List
import discord

from shared import console
import modules.trivia.button as button

BUTTON_EMOJIS: List[str] = ["🇦", "🇧" , "🇨", "🇩"]

class TriviaView(discord.ui.View):
    __interaction: discord.Interaction
    __game: int

    def __init__(self, interaction: discord.Interaction, options: List[str], correct_answer: str, game: int, timeout: float = 180.0):
        super().__init__(timeout=timeout)

        for i, option in enumerate(options):
            print(i, option)
            is_correct: bool = (option == correct_answer)
            self.add_item(button.TriviaButton(label=option, is_correct=is_correct, emoji=BUTTON_EMOJIS[i], row=i))

        self.__interaction = interaction
        self.__game = game

        console.log_debug(f"/trivia: New TriviaView created for game {game}: options = {options}, correct_answer = '{correct_answer}', timeout = {timeout} s.")


    def get_game_id(self) -> int:
        return self.__game


    def disable_buttons(self):
        console.log_debug(f"/trivia: Revealing answers for game {self.__game}...")
        for child in self.children:
            if isinstance(child, button.TriviaButton):
                child.disable()
        console.log_debug(f"/trivia: Answers revealed for game {self.__game}.")


    async def on_timeout(self) -> None:
        console.log(f"/trivia: Game {self.__game} timed out.")
        self.disable_buttons()

        # Edit the original message to show disabled buttons
        await self.__interaction.response.edit_message(view=self)
