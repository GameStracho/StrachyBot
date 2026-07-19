from typing import List, Tuple
import discord
import random

from shared import console, models, bot
import modules.trivia.button as button
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
            self.add_item(button.TriviaButton(
                game_id=self._game.match_id, player_id=self._game.get_player_id(),
                label=label, is_correct=is_correct, emoji=BUTTON_EMOJIS[i], row=i
            ))

        console.log_debug(f"/trivia: New TriviaView created for game {self._game.match_id} with {timeout}s timeout.")


    def disable_buttons(self) -> None:
        self._game.end()

        console.log_debug(f"/trivia: Revealing answers for game {self._game.match_id}...")
        for child in self.children:
            if isinstance(child, button.TriviaButton):
                child.disable()
        console.log_debug(f"/trivia: Answers revealed for game {self._game.match_id}.")


    async def on_timeout(self) -> None:
        if self._game.is_over() or self.message is None:
            return


        console.log_info(f"/trivia: Game {self._game.match_id} timed out.")
        self.disable_buttons()

        embed: discord.Embed = self.message.embeds[0]
        embed.color = discord.Color.darker_grey()
        embed.description = "" # remove timeout countdown

        # hide a second icon appearing above the embed
        embed.set_thumbnail(url="attachment://icon.png")

        strachy_bot = self.message._state._get_client()
        assert isinstance(strachy_bot, bot.StrachyBot)

        async with strachy_bot.db_session_factory() as session:
            await update_match(session=session, match_id=self._game.match_id, status=models.EMatchStatus.TIMEOUT)

        # Edit the original message to show disabled buttons
        await self.message.edit(embed=embed, view=self)
