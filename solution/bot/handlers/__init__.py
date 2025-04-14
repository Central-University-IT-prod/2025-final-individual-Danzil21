from aiogram import Dispatcher, F

from .start import start_router
from .auth import auth_router
from .summary_stat import summary_stat_router
from .campaigns import campaigns_router

def setup_routers(dispatcher: Dispatcher):
    start_router.message.filter(F.chat.type == 'private')
    dispatcher.include_router(start_router)
    dispatcher.include_router(auth_router)
    dispatcher.include_router(summary_stat_router)
    dispatcher.include_router(campaigns_router)