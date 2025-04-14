import traceback
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiohttp import ClientResponseError

from bot.database import Repo
from bot.keyboards import get_start_keyboard
from bot.keyboards.back import back_keyboard
from bot.states.auth import AuthState
from bot.utils.api_sdk import AdvertisingPlatformClient

summary_stat_router = Router()


@summary_stat_router.callback_query(F.data == '/summary_stat')
async def callback_auth(callback: CallbackQuery,
                        repo: Repo,
                        state: FSMContext, api_client: AdvertisingPlatformClient):
    await callback.answer()
    user = await repo.get_user(user_id=callback.from_user.id)
    async with api_client as client:
        stats = await client.get_advertiser_campaigns_stats(user.advertiser_id)
    await callback.message.edit_text(
        f"""
<b>📊 Статистика рекламных кампаний</b>

<b>Охват и активность:</b>
└ 👥 Показы: {stats.impressions_count:,}
└ 🖱 Клики: {stats.clicks_count:,}
└ ✨ Конверсия: {stats.conversion:.2f}%

<b>Расходы:</b>
└ 📈 За показы: {stats.spent_impressions:,.2f} ₽
└ 🎯 За клики: {stats.spent_clicks:,.2f} ₽

<b>💰 Общие затраты:</b> {stats.spent_total:,.2f} ₽

<i>Данные обновлены: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>
""",
        reply_markup=back_keyboard()
    )
    await state.set_state(AuthState.waiting_for_uuid)
