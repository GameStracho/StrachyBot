# Tic-Tac-Toe module

from shared.bot import StrachyBot

from .cogs import TicCog


async def setup(bot: StrachyBot) -> None:
    await bot.add_cog(TicCog(bot))
