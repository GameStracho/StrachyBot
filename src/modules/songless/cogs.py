import traceback

from discord.ext import commands, tasks
from typing_extensions import override

from shared import StrachyBot, db_manager, fetch_api, logger

from .api import APIResponse, APISong
from .models import ESonglessCategory, Playlist
from .repository import create_song

PLAYLISTS: list[Playlist] = [
    Playlist(id=1677006641, title="Hip Hop Hits", category=ESonglessCategory.HIP_HIP)
]


class SonglessCog(commands.Cog):
    _bot: StrachyBot

    def __init__(self, bot: StrachyBot) -> None:
        self._bot = bot

    @override
    async def cog_load(self) -> None:
        """Called automatically when the cog is loaded."""
        self.update_songs.start()

    @override
    async def cog_unload(self) -> None:
        """Called automatically when the cog is unloaded."""
        self.update_songs.cancel()

    async def _fetch_playlist(self, playlist_id: int) -> list[APISong]:
        logger.debug(f"Fetching playlist {playlist_id}...")

        songs: list[APISong] = []
        limit: int = 50
        url: str | None = (
            f"https://api.deezer.com/playlist/{playlist_id}/tracks?index=0&limit={limit}"
        )

        while url:
            try:
                response: APIResponse = await fetch_api(url=url, model_class=APIResponse)

                songs.extend(response.data)
                url = response.next

            except Exception as error:
                logger.error(
                    f"Failed to fetch url {url} with error '{error}'.\n\n{traceback.format_exc()}."
                )
                break

        logger.debug(f"Fetched {len(songs)} songs from playlist {playlist_id}.")
        return songs

    # Run once a week (every 168 hours)
    @tasks.loop(hours=168)
    async def update_songs(self) -> None:
        """Fetch PLAYLISTS and save new songs into the database."""
        logger.info(f"Fetching new songs from playlists {PLAYLISTS}...")

        for playlist in PLAYLISTS:
            for song in await self._fetch_playlist(playlist_id=playlist.id):
                await db_manager.execute(
                    db_func=create_song,
                    song_id=song.id,
                    title=song.title,
                    artist=song.artist.name,
                    category=playlist.category,
                )

        logger.info("Playlists fetched and new songs saved into the database.")

    @update_songs.before_loop
    async def before_update_songs(self) -> None:
        """Wait until the bot is fully logged in before running the loop."""
        await self._bot.wait_until_ready()
