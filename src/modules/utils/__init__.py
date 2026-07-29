# Utils module

from shared.bot import StrachyBot

from .cogs import UtilsCog


async def setup(bot: StrachyBot) -> None:
    await bot.add_cog(UtilsCog(bot))
