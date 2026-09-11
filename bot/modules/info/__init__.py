# Info module

from bot.bot import StrachyBot

from .cog import InfoCog


async def setup(bot: StrachyBot) -> None:
    await bot.add_cog(InfoCog(bot))
