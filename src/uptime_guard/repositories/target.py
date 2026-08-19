from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from uptime_guard.models.target import Target
from uptime_guard.repositories.base import BaseRepository


class TargetRepository(BaseRepository[Target]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Target, session=session)

    async def get_by_user_id(self, user_id: UUID) -> list[Target]:
        stmt = select(Target).where(Target.user_id == user_id).options(selectinload(Target.user))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_targets(self) -> list[Target]:
        stmt = select(Target).where(Target.is_active.is_(True)).options(selectinload(Target.user))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
