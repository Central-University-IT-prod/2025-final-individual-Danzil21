__all__ = ["Repo"]


from bot.database.repository import Repo
from bot.database.models import Base

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


def load_sessionmaker(url: str) -> sessionmaker:
    engine = create_async_engine(url, future=True, pool_pre_ping=True, pool_size=5000
                                 )

    async_sessionmaker = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    return async_sessionmaker
