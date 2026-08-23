import traceback

from discord.ext import commands, tasks
from typing_extensions import override

from shared import StrachyBot, db_manager, fetch_api, logger

from .api import APIResponse, APISong
from .models import ESonglessCategory, Playlist
from .repository import create_song

PLAYLISTS: list[Playlist] = [
    Playlist(id=1677006641, title="Hip Hop Hits", category=ESonglessCategory.HIP_HOP),
    Playlist(id=12547421383, title="2020s Rap", category=ESonglessCategory.HIP_HOP),
    Playlist(id=7662551722, title="'10s Rap", category=ESonglessCategory.HIP_HOP),
    Playlist(id=4676818664, title="2000s Rap", category=ESonglessCategory.HIP_HOP),
    Playlist(id=1724212365, title="'90s Rap", category=ESonglessCategory.HIP_HOP),
    Playlist(id=5172233424, title="80's Rap", category=ESonglessCategory.HIP_HOP),
    Playlist(id=752286631, title="Rock Hits", category=ESonglessCategory.ROCK),
    Playlist(id=13693489781, title="2020s Rock", category=ESonglessCategory.ROCK),
    Playlist(id=1057779131, title="2010s Rock", category=ESonglessCategory.ROCK),
    Playlist(id=1419215845, title="2000s Rock", category=ESonglessCategory.ROCK),
    Playlist(id=1728093421, title="90s Rock", category=ESonglessCategory.ROCK),
    Playlist(id=8621268482, title="80s Rock", category=ESonglessCategory.ROCK),
    Playlist(id=1405240385, title="70s Rock", category=ESonglessCategory.ROCK),
    Playlist(id=1437011185, title="60s Rock", category=ESonglessCategory.ROCK),
    Playlist(id=3155776842, title="Top Worldwide", category=ESonglessCategory.ALL),
    Playlist(id=2098157264, title="Global Hits", category=ESonglessCategory.ALL),
    Playlist(id=13650203641, title="20s Pop", category=ESonglessCategory.ALL),
    Playlist(id=8282573142, title="10s Pop", category=ESonglessCategory.ALL),
    Playlist(id=8326097522, title="00s Pop", category=ESonglessCategory.ALL),
    Playlist(id=8311123682, title="90s Pop", category=ESonglessCategory.ALL),
    Playlist(id=8512471762, title="80s Pop", category=ESonglessCategory.ALL),
    Playlist(id=756018311, title="70s Pop", category=ESonglessCategory.ALL),
    Playlist(id=8962730322, title="60s Pop", category=ESonglessCategory.ALL),
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
                    f"Failed to fetch url {url} with error '{error}'.\n{traceback.format_exc()}."
                )
                break

        logger.debug(f"Fetched {len(songs)} songs from playlist {playlist_id}.")
        return songs

    # Run once a week (every 168 hours)
    @tasks.loop(hours=168)
    async def update_songs(self) -> None:
        """Fetch PLAYLISTS and save new songs into the database."""
        logger.info(f"Fetching new songs from playlists {PLAYLISTS}...")
        added: int = 0

        try:
            for playlist in PLAYLISTS:
                for song in await self._fetch_playlist(playlist_id=playlist.id):
                    if not song.readable:
                        continue

                    song_added: bool | None = await db_manager.execute(
                        db_func=create_song,
                        song_id=song.id,
                        title=song.title,
                        artist=song.artist.name,
                        category=playlist.category,
                    )

                    if song_added:
                        added += 1
        except Exception as error:
            logger.error(
                f"Failed to fetch playlists with error '{error}'. \n{traceback.format_exc}."
            )

        logger.info(f"Playlists fetched and {added} new songs saved into the database.")

    @update_songs.before_loop
    async def before_update_songs(self) -> None:
        """Wait until the bot is fully logged in before running the loop."""
        await self._bot.wait_until_ready()
