from typing import List, Tuple
import discord
import random

from shared import console
import modules.trivia.button as button
from .game import TriviaGame

BUTTON_EMOJIS: List[str] = ["🇦", "🇧" , "🇨", "🇩"]

class TriviaView(discord.ui.View):
    _interaction: discord.Interaction
    _game: TriviaGame
    message: discord.Message | None

    def __init__(self, game: TriviaGame, timeout: float = 10.0):
        super().__init__(timeout=timeout)

        self._game = game

        options: List[Tuple[str, bool]] = [(self._game.get_correct_answer(), True)]

        for incorrect_answer in self._game.get_incorrect_answers():
            options.append((incorrect_answer, False))

        random.shuffle(options)

        print(len(options))

        for i, option in enumerate(options):
            print(i, option)
            label, is_correct = option
            self.add_item(button.TriviaButton(game_id=self._game.get_game_id(), label=label, is_correct=is_correct, emoji=BUTTON_EMOJIS[i], row=i))

        console.log_debug(f"/trivia: New TriviaView created for game {self._game.get_game_id()} with {timeout}s timeout.")


    def disable_buttons(self):
        self._game.end()

        console.log_debug(f"/trivia: Revealing answers for game {self._game.get_game_id()}...")
        for child in self.children:
            if isinstance(child, button.TriviaButton):
                child.disable()
        console.log_debug(f"/trivia: Answers revealed for game {self._game.get_game_id()}.")


    async def on_timeout(self) -> None:
        if self._game.is_over() or self.message is None:
            return


        console.log_info(f"/trivia: Game {self._game.get_game_id()} timed out.")
        self.disable_buttons()

        embed: discord.Embed = self.message.embeds[0]
        embed.add_field(name="Result", value="Timed out! ⏰", inline=False)
        embed.color = discord.Color.darker_grey()
        embed.description = "" # remove timeout countdown

        # Edit the original message to show disabled buttons
        await self.message.edit(embed=embed, view=self)
