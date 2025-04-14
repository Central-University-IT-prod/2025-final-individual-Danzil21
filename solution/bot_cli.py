import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.middlewares import DBMiddleware
from bot.handlers import setup_routers
from bot.database import load_sessionmaker
from app.core.config import settings
from bot.utils.api_sdk import AdvertisingPlatformClient

logger = logging.getLogger(__name__)

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DATABASE}"
)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger.error("Starting bot")


    sessionmaker = load_sessionmaker(DATABASE_URL)

    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())
    dp['api_client'] = AdvertisingPlatformClient(base_url='http://backend:8080')


    setup_routers(dp)

    dp.update.outer_middleware.register(
        DBMiddleware(sessionmaker=sessionmaker)
    )

    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query"]
        )
    finally:
        await dp.storage.close()
        await bot.session.close()


def cli():
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")


if __name__ == '__main__':
    cli()
