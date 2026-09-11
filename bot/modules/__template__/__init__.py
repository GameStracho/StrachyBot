from shared import StrachyBot

from .cog import Cog


async def setup(bot: StrachyBot) -> None:
    await bot.add_cog(Cog(bot=bot))
