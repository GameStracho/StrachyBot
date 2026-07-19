# Trivia module

from shared.bot import StrachyBot
from .cogs import TriviaCog

async def setup(bot: StrachyBot) -> None:
    await bot.add_cog(TriviaCog(bot))
