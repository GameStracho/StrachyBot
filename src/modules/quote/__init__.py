# Quote module

from shared.bot import StrachyBot
from .cogs import QuoteCog

async def setup(bot: StrachyBot) -> None:
    await bot.add_cog(QuoteCog(bot))
