from sqlalchemy.ext.asyncio import AsyncSession

import console

from .models import CommandLog


async def create_command_log(session: AsyncSession, user_id: int, command_name: str) -> int:
    """
    Creates a new command log record in the database.

    Returns id of the created record.
    """

    console.log_debug(
        f"shared: Creating a new command log "
        f"(user_id = {user_id}, command_name = {command_name})..."
    )
    record_id: int = 0

    async with session.begin():
        record: CommandLog = CommandLog(user_id=user_id, command_name=command_name)
        session.add(record)
        record_id = record.id

    console.log_debug(f"wordle: New command log ({record_id}) created.")
    return record_id
