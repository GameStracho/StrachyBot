import hashlib
from datetime import UTC, date, datetime, time
import unicodedata

def strip_accents(text: str) -> str:
    """Normalizes string by removing diacritical marks/accents in Python."""
    nfkd_form = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import logger
from shared.models import EMatchStatus, Match

from .models import ESonglessCategory, SonglessMatch, SonglessSong


async def create_song(
    session: AsyncSession,
    song_id: int,
    title: str,
    artist: str,
    category: ESonglessCategory,
) -> bool:
    """
    Creates a new songless song record in the database.

    Returns True if the record was created, False otherwise.
    """

    logger.debug(
        f"songless: Creating a new song (song_id = {song_id}, title = {title}, "
        f"artist = {artist}, category = {category})..."
    )

    async with session.begin():
        existing_song: SonglessSong | None = (
            await session.execute(
                select(SonglessSong).where(
                    or_(
                        SonglessSong.id == song_id,
                        and_(SonglessSong.title == title, SonglessSong.artist == artist),
                    )
                )
            )
        ).scalar()

        if existing_song:
            logger.debug(
                f"songless: Song '{title}' ({song_id}) already exists. "
                f"Skipping addition to database."
            )
            return False

        song: SonglessSong = SonglessSong(id=song_id, title=title, artist=artist, category=category)
        session.add(song)

    logger.debug(f"songless: New song '{title}' ({song_id}) created.")
    return True


async def create_match(
    session: AsyncSession,
    player_id: int,
    song_id: int,
    category: ESonglessCategory,
    is_daily: bool,
) -> int:
    """
    Creates a new songless match record in the database.

    Returns id of the created match.
    """

    logger.debug(
        f"songless: Creating a new match (player_id = {player_id}, song_id = {song_id}, "
        f"category = {category}, is_daily = {is_daily})..."
    )
    match_id: int = 0

    async with session.begin():
        parent_match: Match = Match(player_id=player_id)
        session.add(parent_match)

        # Flush pushes the record to Postgres temporarily to generate the auto-increment ID
        # without closing or committing the transaction yet.
        await session.flush()

        child_match: SonglessMatch = SonglessMatch(
            match_id=parent_match.match_id, song_id=song_id, category=category, is_daily=is_daily
        )
        session.add(child_match)

        match_id = parent_match.match_id

    logger.debug(f"songless: New match ({match_id}) created.")
    return match_id


async def update_match(
    session: AsyncSession,
    match_id: int,
    status: EMatchStatus,
    guesses_count: int,
    guesses: list[int | None],
) -> bool:
    """
    Updates an pending songless match record in the database.

    Returns true on success.
    """
    logger.debug(
        f"songless: Updating match ({match_id}) "
        f"with status ({status}) and {guesses_count} guesses ({guesses})..."
    )

    async with session.begin():
        parent_match: Match | None = (
            await session.execute(select(Match).where(Match.match_id == match_id))
        ).scalar_one_or_none()

        child_match: SonglessMatch | None = (
            await session.execute(select(SonglessMatch).where(SonglessMatch.match_id == match_id))
        ).scalar_one_or_none()

        if not parent_match or not child_match:
            logger.error(f"songless: Match ({match_id}) not found, update aborted.")
            return False

        if parent_match.status != EMatchStatus.PENDING:
            logger.error("songless: Only 'pending' matches can be updated.")
            return False

        parent_match.status = status
        child_match.guesses_count = guesses_count
        child_match.guesses = guesses

    logger.debug(f"songless: Match ({match_id}) updated.")

    return True


async def has_played_daily_challenge(
    session: AsyncSession,
    player_id: int,
    category: ESonglessCategory,
    target_date: date | None = None,
) -> bool:
    """
    Checks whether a player has already started or played the
    category's daily challenge on a specific date.
    """
    if target_date is None:
        target_date = datetime.now(tz=UTC).date()

    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)

    wordle_matches = (
        select(func.count())
        .select_from(SonglessMatch)
        .join(Match, SonglessMatch.match_id == Match.match_id)
        .where(
            Match.player_id == player_id,
            SonglessMatch.is_daily.is_(True),
            SonglessMatch.category == category,
            Match.start_time >= start_of_day,
            Match.start_time <= end_of_day,
        )
    )

    result = await session.execute(wordle_matches)
    count = result.scalar() or 0
    return count > 0


async def get_song_by_id(
    session: AsyncSession,
    song_id: int,
) -> SonglessSong | None:
    """Fetches a single song by its unique ID."""
    result = await session.execute(select(SonglessSong).where(SonglessSong.id == song_id))
    return result.scalar_one_or_none()


async def search_songs_by_query(
    session: AsyncSession,
    raw_query: str,
    category: ESonglessCategory | None = None,
    limit: int = 25,
) -> list[SonglessSong]:
    """
    Fetches up to 25 songs matching a search string in their title and/or artist name.
    Case-insensitive search via icontains/ilike.
    """
    norm_query: str = raw_query.replace(" - ", " ")
    norm_query = norm_query.replace("- ", " ")
    norm_query = norm_query.replace(" -", " ")

    norm_query = helpers.strip_accents(norm_query)
    norm_title = func.unaccent(SonglessSong.title)
    norm_artist = func.unaccent(SonglessSong.artist)

    # Create concatenated column expressions
    title_artist = func.concat(norm_title, " ", norm_artist)
    artist_title = func.concat(norm_artist, " ", norm_title)

    query = select(SonglessSong).where(
        or_(
            norm_title.icontains(norm_query),
            norm_artist.icontains(norm_query),
            title_artist.icontains(norm_query),
            artist_title.icontains(norm_query),
        )
    )

    if category:
        query = query.where(SonglessSong.category == category)

    query = query.limit(limit)

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_daily_song(
    session: AsyncSession,
    target_date: date | None = None,
    category: ESonglessCategory | None = None,
) -> SonglessSong | None:
    """
    Returns a deterministic 'random' song based on a specific date.
    Everyone calling this function on the same day with the same category
    will receive the exact same song.
    """
    if target_date is None:
        target_date = datetime.now(tz=UTC).date()

    # Create a unique seed string for this date + category combination
    seed_str = f"{target_date.isoformat()}:{category.value if category else 'ALL'}"

    # Convert the string hash into a float between -1.0 and 1.0 for PostgreSQL setseed()
    hash_val = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    seed_float = (hash_val / (2**128 - 1)) * 2 - 1

    # Set PostgreSQL random seed for the current session transaction
    await session.execute(select(func.setseed(seed_float)))

    return await get_random_song(session=session, category=category)


async def get_random_song(
    session: AsyncSession,
    category: ESonglessCategory | None = None,
) -> SonglessSong | None:
    """Returns a single random song from the database."""
    query = select(SonglessSong).order_by(func.random())

    if category is not None:
        query = query.where(SonglessSong.category == category)

    result = await session.execute(query.limit(1))
    return result.scalar_one_or_none()


async def get_recent_pending_match(
    session: AsyncSession,
    player_id: int,
) -> tuple[Match, SonglessMatch] | None:
    """
    Returns the most recent pending songless match
    along with its parent Match record for a given player.
    """
    query = (
        select(Match, SonglessMatch)
        .join(SonglessMatch, Match.match_id == SonglessMatch.match_id)
        .where(
            Match.player_id == player_id,
            Match.status == EMatchStatus.PENDING,
        )
        .order_by(Match.start_time.desc())
        .limit(1)
    )

    result = await session.execute(query)
    record = result.first()
    return (record[0], record[1]) if record else None
