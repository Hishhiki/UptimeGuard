from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from uptime_guard.models.check_log import CheckLog
from uptime_guard.repositories.base import BaseRepository


class CheckLogRepository(BaseRepository[CheckLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=CheckLog, session=session)

    async def get_by_target_id(self, target_id: UUID, limit=100) -> list[CheckLog]:
        stmt = (
            select(CheckLog)
            .where(CheckLog.target_id == target_id)
            .order_by(CheckLog.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
