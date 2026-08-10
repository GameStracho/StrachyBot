# Wordle module

from shared import StrachyBot

from .cogs import WordleCog


async def setup(bot: StrachyBot) -> None:
    await bot.add_cog(WordleCog(bot))
