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
    record: CommandLog = CommandLog(user_id=user_id, command_name=command_name)

    async with session.begin():
        session.add(record)

    console.log_debug(f"shared: New command log ({record.id}) created.")
    return record.id
