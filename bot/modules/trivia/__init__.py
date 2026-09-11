# Trivia module

from bot.bot import StrachyBot

from .cog import TriviaCog


async def setup(bot: StrachyBot) -> None:
    await bot.add_cog(TriviaCog(bot=bot))
