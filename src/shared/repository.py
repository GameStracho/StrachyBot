from datetime import datetime
from typing import Any, cast

from sqlalchemy import CursorResult, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import CommandLog, Log


async def create_command_log(session: AsyncSession, user_id: int, command_name: str) -> int:
    """
    Creates a new command log record in the database.

    Returns id of the created record.
    """
    record: CommandLog = CommandLog(user_id=user_id, command_name=command_name)

    async with session.begin():
        session.add(record)

    return record.id


async def create_log(session: AsyncSession, level: str, module: str, message: str) -> int:
    """
    Creates a new log record in the database.

    Returns id of the created record.
    """
    record: Log = Log(level=level, module=module, message=message)

    async with session.begin():
        session.add(record)

    return record.id


async def delete_expired_logs(session: AsyncSession, cutoff: datetime) -> int:
    statement = delete(Log).where(Log.created_at < cutoff)
    result: CursorResult[Any] = cast(CursorResult[Any], await session.execute(statement))
    await session.commit()

    return result.rowcount
