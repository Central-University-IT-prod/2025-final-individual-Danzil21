from typing import Union, Type

from sqlalchemy.ext.asyncio import AsyncSession

from api.database.models.models import *


class Repo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_client(self, client_id: str) -> Union[Type[Client], None]:
        return await self.session.get(Client, client_id)