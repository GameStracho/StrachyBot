import os
from dotenv import load_dotenv
import asyncio

from shared import console

profile: str = os.getenv("COMPOSE_PROFILES", "development")

if profile == "development":
    load_dotenv()
    console.log_debug("Environment variables loaded.")

from shared.bot import StrachyBot

async def main() -> None:
    token: str | None = os.getenv("DISCORD_TOKEN")

    if token is None:
        console.log_error("Could not load discord token.")
        return

    bot = StrachyBot()
    await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.log_info("Shutdown requested. Closing bot...")
