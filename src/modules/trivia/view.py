from typing import List
import discord

from shared import console
import modules.trivia.button as button

BUTTON_EMOJIS: List[str] = ["🇦", "🇧" , "🇨", "🇩"]

class TriviaView(discord.ui.View):
    _interaction: discord.Interaction
    _game: int
    message: discord.Message | None
    _game_ended: bool = False

    def __init__(self, options: List[str], correct_answer: str, game: int, timeout: float = 5.0):
        super().__init__(timeout=timeout)

        for i, option in enumerate(options):
            print(i, option)
            is_correct: bool = (option == correct_answer)
            self.add_item(button.TriviaButton(label=option, is_correct=is_correct, emoji=BUTTON_EMOJIS[i], row=i))

        self._game = game

        console.log_debug(f"/trivia: New TriviaView created for game {game}: options = {options}, correct_answer = '{correct_answer}', timeout = {timeout} s.")


    def get_game_id(self) -> int:
        return self._game


    def disable_buttons(self):
        self._game_ended = True

        console.log_debug(f"/trivia: Revealing answers for game {self._game}...")
        for child in self.children:
            if isinstance(child, button.TriviaButton):
                child.disable()
        console.log_debug(f"/trivia: Answers revealed for game {self._game}.")


    async def on_timeout(self) -> None:
        if self._game_ended or self.message is None:
            return

        console.log_info(f"/trivia: Game {self._game} timed out.")
        self.disable_buttons()

        # Edit the original message to show disabled buttons
        await self.message.edit(view=self)
