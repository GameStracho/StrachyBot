import asyncio
import os
import sys

# Ensure the project root is on sys.path when running this file directly
# (e.g. `python bot/main.py`), so that `shared`, `bot`, etc. are importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from bot.bot import StrachyBot
from shared import logger


async def main() -> None:
    profile: str = os.getenv("COMPOSE_PROFILES", "development")

    if profile in ("development", "bot"):
        load_dotenv()
        logger.debug("Environment variables loaded.")

    token: str | None = os.getenv("DISCORD_TOKEN")

    if token is None:
        logger.critical("Could not load discord token. Please set DISCORD_TOKEN.")
        return

    bot = StrachyBot()

    try:
        await bot.start(token)
    except asyncio.CancelledError:
        logger.info("Shutdown requested. Closing bot...")
    finally:
        if not bot.is_closed():
            logger.info("Closing bot HTTP session and active connections...")
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
