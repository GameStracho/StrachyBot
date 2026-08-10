import asyncio
import os

from dotenv import load_dotenv

import console
from shared.bot import StrachyBot


async def main() -> None:
    profile: str = os.getenv("COMPOSE_PROFILES", "development")

    if profile == "development":
        load_dotenv()
        console.log_debug("Environment variables loaded.")

    token: str | None = os.getenv("DISCORD_TOKEN")

    if token is None:
        console.log_error("Could not load discord token.")
        return

    bot = StrachyBot()
    bot.create_db_session_factory()

    try:
        await bot.start(token)
    except asyncio.CancelledError:
        console.log_info("Shutdown requested. Closing bot...")
    finally:
        if not bot.is_closed():
            console.log_info("Closing bot HTTP session and active connections...")
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
