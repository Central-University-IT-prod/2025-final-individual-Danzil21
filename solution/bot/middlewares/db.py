import os
import sys
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update

from sqlalchemy.orm import sessionmaker

from bot.database import Repo


class DBMiddleware(BaseMiddleware):
    def __init__(self, sessionmaker: sessionmaker) -> None:
        self.sessionmaker = sessionmaker

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        async with self.sessionmaker() as session:
            data["repo"] = Repo(session)
            return await handler(event, data)
