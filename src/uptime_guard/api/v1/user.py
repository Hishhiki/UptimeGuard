from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from uptime_guard.database import get_session
from uptime_guard.models.user import User
from uptime_guard.repositories.user import UserRepository
from uptime_guard.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
async def get_users(session: AsyncSession = Depends(get_session)) -> list[User]:
    repo = UserRepository(session)
    result = await repo.list_all()
    if not result:
        return []
    return result


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: UUID, session: AsyncSession = Depends(get_session)) -> User:
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def user_delete(user_id: UUID, session: AsyncSession = Depends(get_session)) -> None:
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await repo.delete(user)
