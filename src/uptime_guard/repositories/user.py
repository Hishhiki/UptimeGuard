from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from uptime_guard.models.user import User
from uptime_guard.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Репозиторий для работы с пользователями."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=User, session=session)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Найти пользователя по его цифровому telegram_id."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
