from typing import Union, Type, Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.models import *


class Repo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: int) -> Union[Type[BotUser], None]:
        return await self.session.get(BotUser, user_id)

    async def create_user(self, user_id: int) -> Type[BotUser] | Any:
        existing_user = await self.get_user(user_id)

        if existing_user:
            return existing_user

        user = BotUser(user_id=user_id)

        self.session.add(user)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()

        return user

    async def get_campaign_count_by_advertiser_id(self, advertiser_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Campaign)
            .where(Campaign.advertiser_id == advertiser_id)
            .where(Campaign.is_deleted == False)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0