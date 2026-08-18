from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from uptime_guard.database import get_session
from uptime_guard.models.target import Target
from uptime_guard.repositories.target import TargetRepository
from uptime_guard.schemas.target import TargetCreate, TargetResponse

router = APIRouter(prefix="/targets", tags=["targets"])

@router.post("/", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    body: TargetCreate,
    session: AsyncSession = Depends(get_session),
) -> Target:
    repo = TargetRepository(session)
    #TODO
    new_target = Target(
        url=str(body.url),
        method=body.method,
        expected_status=body.expected_status,
        interval_seconds=body.interval_seconds,
        timeout=body.timeout,
    )
    return await repo.create(new_target)



@router.get("/", response_model = list[TargetResponse])
async def get_targets(
    session: AsyncSession = Depends(get_session)
) -> list[Target]:
    repo = TargetRepository(session)
    return await repo.list_all()


@router.get("/{target_id}", response_model = TargetResponse)
async def get_target_by_id(target_id:UUID, session: AsyncSession = Depends(get_session)) -> Target:
    repo = TargetRepository(session)
    target = await repo.get_by_id(target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    return target


@router.patch("/{target_id}",response_model = TargetResponse)
async def update_target(target_id:UUID, session:AsyncSession= Depends(get_session)) -> Target:
    repo = TargetRepository(session)
    target = await repo.get_by_id(target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    target.is_active = not target.is_active
    await session.commit()
    await session.refresh(target)
    return target

@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(target_id:UUID, session:AsyncSession = Depends(get_session)) ->None:
    repo = TargetRepository(session)
    target = await repo.get_by_id(target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    await repo.delete(target)
