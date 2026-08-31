import traceback

import discord
from discord import app_commands
from discord.ext import commands, tasks
from typing_extensions import override

from shared import StrachyBot, api, db_manager, logger, models, ui

from .api import APIResponse, APISong
from .game import Game
from .models import ESonglessCategory, Playlist, SonglessMatch
from .repository import create_song, get_recent_pending_match, search_songs_by_query, has_played_daily_challenge
from .ui import View, active_game_views

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
                response: APIResponse = await api.fetch_model(url=url, model_class=APIResponse)

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
        logger.info(f"Fetching new songs from {len(PLAYLISTS)} playlists...")
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

    @app_commands.command(name="songless", description="Try to guess a song in 6 tries.")
    async def songless(
        self,
        interaction: discord.Interaction,
        category: ESonglessCategory = ESonglessCategory.ALL,
        daily_challenge: bool = False,
    ) -> None:
        try:
            user = ui.get_user(user=interaction.user)
            logger.debug(f"Command '/songless' used by user {user}.")

            if daily_challenge and await db_manager.execute(
                db_func=has_played_daily_challenge, player_id=interaction.user.id, category=category
            ):
                logger.info(f"User {user} already played today's daily challenge in category {category}.")

                embed, icon = ui.embed.build_warning(
                    message=f"You already played today's daily challenge in category {category}."
                )

                await interaction.response.send_message(embed=embed, file=icon, ephemeral=True)
                return

            # Tells Discord to display "Thinking..." and extends time limit to 15 mins
            await interaction.response.defer()

            game: Game = Game(player=user, category=category, is_daily=daily_challenge)
            await game.start()

            view: View = View(game=game, timeout=300.0)
            embed, files = view.build_embed()

            logger.info(f"New {game} started by user {user}")

            # CRITICAL: Save the sent message to the view so the timeout handler can edit it!
            await interaction.followup.send(embed=embed, view=view, files=files)
            view.message = await interaction.original_response()
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)

    async def song_autocomplete(
        self, interaction: discord.Interaction, query: str
    ) -> list[app_commands.Choice[int]]:
        """Provides up to 25 title/artist suggestions for the guess command."""

        songs = await db_manager.execute(
            db_func=search_songs_by_query, query_str=query.strip(), limit=25
        )

        if not songs:
            return []

        def truncate_name(title: str, artist: str, max_length: int = 100) -> str:
            full_name = f"{title} - {artist}"
            if len(full_name) <= max_length:
                return full_name
            return f"{full_name[: max_length - 3]}..."

        return [
            app_commands.Choice(
                # Discord limit is 100 characters
                name=truncate_name(title=song.title, artist=song.artist, max_length=100),
                value=song.id,
            )
            for song in songs
        ]

    @app_commands.command(
        name="songless-guess", description="Submit a song guess for your most recent active game."
    )
    @app_commands.autocomplete(song=song_autocomplete)
    async def guess(self, interaction: discord.Interaction, song: int) -> None:
        try:
            user = ui.get_user(user=interaction.user)
            logger.debug(f"Command '/songless-guess' used by user {user} with song_id {song}.")

            game: tuple[models.Match, SonglessMatch] | None = await db_manager.execute(
                db_func=get_recent_pending_match, player_id=user.id
            )

            if not game or not active_game_views.get(game[0].match_id):
                warning_embed, warning_icon = ui.embed.build_warning(
                    "No active game found. Use command `/songless` to start a new game."
                )
                await interaction.response.send_message(
                    embed=warning_embed, file=warning_icon, ephemeral=True
                )

                logger.debug(f"No active game found for user {user}.")
                return

            view: View = active_game_views[game[0].match_id]
            default_status: str = "Guess submitted."
            guess = None

            if song in view.game.guesses:
                logger.debug(f"User {user} already guessed song {song}.")
                default_status = "You already guessed that song."
            else:
                guess = await view.game.submit_guess(song_id=song)
                logger.info(
                    f"User {user} submitted {guess[1]} guess "
                    f"'{guess[0].title} - {guess[0].artist}' ({song})."
                )

            assert view.message
            embed: discord.Embed = ui.embed.extract(target=view.message, index=0, hide_icon=True)
            view.update_embed(embed=embed, default_status=default_status, last_guess=guess)

            if not guess:
                await view.message.edit(embed=embed, view=view)
            else:
                icon, icon_url = ui.load_attachment(path=__file__, filename="icon.png")
                embed.set_thumbnail(url=icon_url)
                files: list[discord.File] = [icon]

                if view.game.status == models.EMatchStatus.PENDING:
                    files.append(discord.File(fp=view.game.snippet, filename="snippet.mp3"))

                await view.message.edit(embed=embed, view=view, attachments=files)

            await interaction.response.send_message(
                "Guess submitted.", ephemeral=True, delete_after=0.0
            )
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
