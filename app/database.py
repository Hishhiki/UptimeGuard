from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings

engine = create_async_engine(settings.database_url)
session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with session_factory() as session:
        yield session