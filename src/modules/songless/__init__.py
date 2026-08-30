# Songless module
import static_ffmpeg

from shared import StrachyBot


async def setup(bot: StrachyBot) -> None:
    # Download portable ffmpeg libraries to Python before importing the cog,
    # as pydub relies on ffmpeg being available at import time.
    static_ffmpeg.add_paths()

    from .cogs import SonglessCog

    await bot.add_cog(SonglessCog(bot=bot))
