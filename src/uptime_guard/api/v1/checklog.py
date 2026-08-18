from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from uptime_guard.database import get_session
from uptime_guard.models.check_log import CheckLog
from uptime_guard.repositories.check_log import CheckLogRepository
from uptime_guard.schemas.checklog import CheckLogResponse

router = APIRouter(prefix="/targets", tags=["check_logs"])


@router.get("/{target_id}/logs", response_model=list[CheckLogResponse])
async def get_logs(
    target_id: UUID, session: AsyncSession = Depends(get_session)
) -> list[CheckLog]:
    repo = CheckLogRepository(session)
    result = await repo.get_by_target_id(target_id)
    if not result:
        return []
    return result
