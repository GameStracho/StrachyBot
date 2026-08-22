# Songless module
import static_ffmpeg

from shared import StrachyBot

from .cogs import SonglessCog


async def setup(bot: StrachyBot) -> None:
    # Download portable ffmpeg libraries to Python
    static_ffmpeg.add_paths()

    await bot.add_cog(SonglessCog(bot=bot))
