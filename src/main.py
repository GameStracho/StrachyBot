import asyncio
import os

from dotenv import load_dotenv

from shared import StrachyBot, logger


async def main() -> None:
    profile: str = os.getenv("COMPOSE_PROFILES", "development")

    if profile == "development":
        load_dotenv()
        logger.debug("Environmental variables loaded.")

    token: str | None = os.getenv("DISCORD_TOKEN")

    if token is None:
        logger.critical("Could not load discord token.")
        return

    bot = StrachyBot()
    bot.create_db_session_factory()

    try:
        await bot.start(token)
    except asyncio.CancelledError:
        logger.info("Shutdown requested. Closing bot...")
    finally:
        if not bot.is_closed():
            logger.info("Closing bot HTTP session and active connections...")
            await bot.close()


if __name__ == "__main__":
    # asyncio.run(main())

    logger.debug("Debug message.")
    logger.info("Info message.")
    logger.warning("Warning message.")
    logger.error("Error message.")
    logger.critical("Critical message.")
