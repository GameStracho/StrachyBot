# Info module

from shared import StrachyBot

from .cogs import InfoCog


async def setup(bot: StrachyBot) -> None:
    await bot.add_cog(InfoCog(bot))
