import io
import os
import traceback
from datetime import datetime

import aiohttp
import matplotlib.pyplot as plt
import numpy as np
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile, InputFile, BufferedInputFile

from api.utils.upload_file import upload_cdn_fileobj
from bot.database import Repo
from bot.keyboards.back import campaign_back_keyboard, back_keyboard
from bot.keyboards.campaigns import get_navigation_keyboard, CampaignPageCallbackData, CampaignCallbackData, \
    campaign_keyboard, PARAM_SHORT_MAP, CampaignEditCallbackData, CampaignStatsCallbackData
from bot.states.auth import AuthState
from bot.states.campaign_edit import CampaignEditState
from bot.utils.api_sdk import AdvertisingPlatformClient, CampaignUpdate, CampaignResponse
from bot.utils.campaigns import PARAM_EDIT_INSTRUCTIONS, VALIDATION_MESSAGES, format_campaign_message, get_param_name

campaigns_router = Router()


@campaigns_router.callback_query(F.data == '/campaigns')
async def callback_auth(callback: CallbackQuery,
                        repo: Repo,
                        state: FSMContext, api_client: AdvertisingPlatformClient):
    await callback.answer()
    user = await repo.get_user(user_id=callback.from_user.id)
    cmpg_count = await repo.get_campaign_count_by_advertiser_id(user.advertiser_id)
    async with api_client as client:
        campaigns = await client.list_campaigns(user.advertiser_id)

    await callback.message.edit_text(
        f"""
<b>🪙  Рекламные кампании</b>

Найдено кампаний: {cmpg_count}
""",
        reply_markup=get_navigation_keyboard(0, cmpg_count, campaigns)
    )
    await state.set_state(AuthState.waiting_for_uuid)


@campaigns_router.callback_query(F.data == '/campaigns/create')
async def callback_auth(callback: CallbackQuery,
                        repo: Repo,
                        state: FSMContext, api_client: AdvertisingPlatformClient):
    await callback.answer()
    user = await repo.get_user(user_id=callback.from_user.id)

    await callback.message.edit_text(
        """Отправьте json для создания кампании

Пример:
{
  "impressions_limit": 0,
  "clicks_limit": 0,
  "cost_per_impression": 0,
  "cost_per_click": 0,
  "ad_title": "string",
  "ad_text": "string",
  "start_date": 0,
  "end_date": 0,
  "targeting": {
    "gender": "MALE",
    "age_from": 0,
    "age_to": 0,
    "location": "string"
  }
}
""", reply_markup=back_keyboard()
    )
    await state.set_state(AuthState.waiting_for_json)


@campaigns_router.callback_query(CampaignPageCallbackData.filter())
async def callback_auth(callback: CallbackQuery,
                        callback_data: CampaignPageCallbackData,
                        repo: Repo,
                        state: FSMContext, api_client: AdvertisingPlatformClient):
    await callback.answer()
    offset = callback_data.offset
    user = await repo.get_user(user_id=callback.from_user.id)
    cmpg_count = await repo.get_campaign_count_by_advertiser_id(user.advertiser_id)
    async with api_client as client:
        campaigns = await client.list_campaigns(user.advertiser_id, page=offset + 1)

    await callback.message.edit_text(
        f"""
<b>🪙  Рекламные кампании</b>

Найдено кампаний: {cmpg_count}
""",
        reply_markup=get_navigation_keyboard(offset, cmpg_count, campaigns)
    )
    await state.set_state(AuthState.waiting_for_uuid)


@campaigns_router.callback_query(CampaignCallbackData.filter())
async def callback_auth(callback: CallbackQuery,
                        callback_data: CampaignCallbackData,
                        repo: Repo,
                        state: FSMContext, api_client: AdvertisingPlatformClient):
    await callback.answer()
    campaign_id = callback_data.campaign_id
    offset = callback_data.offset
    user = await repo.get_user(user_id=callback.from_user.id)
    async with api_client as client:
        campaign = await client.get_campaign(advertiser_id=user.advertiser_id, campaign_id=campaign_id)

    try:
        await callback.message.edit_text(format_campaign_message(campaign),
            reply_markup=campaign_keyboard(offset, campaign)
        )
    except TelegramBadRequest as e:
        await callback.message.delete()
        await callback.message.answer(format_campaign_message(campaign),
                                         reply_markup=campaign_keyboard(offset, campaign)
                                         )
    await state.set_state(AuthState.waiting_for_uuid)


@campaigns_router.callback_query(CampaignEditCallbackData.filter())
async def edit_campaign_param_callback(
        callback: CallbackQuery,
        callback_data: CampaignEditCallbackData,
        state: FSMContext
):
    await state.update_data(
        campaign_id=callback_data.campaign_id,
        param=callback_data.p,
        offset=callback_data.off
    )

    full_param = None
    for key, short in PARAM_SHORT_MAP.items():
        if short == callback_data.p:
            full_param = key
            break

    if not full_param:
        await callback.message.answer("❌ Ошибка: неизвестный параметр",
                                      reply_markup=campaign_back_keyboard(offset=callback_data.off, campaign_id=callback_data.campaign_id))
        await state.clear()
        return

    param_info = PARAM_EDIT_INSTRUCTIONS[full_param]

    instruction_message = f"""
<b>✏️ Редактирование параметра: {param_info['name']}</b>

<i>{param_info['description']}</i>

📝 Формат ввода: {param_info['format']}
💡 Пример: <code>{param_info['example']}</code>

Введите новое значение:"""

    await callback.message.edit_text(instruction_message,
                                  reply_markup=campaign_back_keyboard(offset=callback_data.off, campaign_id=callback_data.campaign_id))
    await state.set_state(CampaignEditState.waiting_for_new_value)
    await callback.answer()


@campaigns_router.message(CampaignEditState.waiting_for_new_value, F.text)
async def process_campaign_edit_value(
        message: Message,
        state: FSMContext,
        api_client: AdvertisingPlatformClient,
        repo: Repo
):
    data = await state.get_data()
    campaign_id = data.get("campaign_id")
    param_short = data.get("param")
    offset = data.get("offset")
    new_value = message.text.strip()

    full_param = None
    for key, short in PARAM_SHORT_MAP.items():
        if short == param_short:
            full_param = key
            print(key)
            break
    if not full_param:
        await message.answer("❌ Ошибка: неизвестный параметр",
                             reply_markup=campaign_back_keyboard(offset=offset, campaign_id=campaign_id))
        await state.clear()
        return

    update_data = {}

    if full_param in ["impressions_limit", "clicks_limit", "start_date", "end_date"]:
        try:
            new_value = int(new_value)
        except ValueError:
            await message.answer(VALIDATION_MESSAGES["integer"],
                                 reply_markup=campaign_back_keyboard(offset=offset, campaign_id=campaign_id))
            return
    elif full_param in ["cost_per_impression", "cost_per_click"]:
        try:
            new_value = float(new_value)
        except ValueError:
            await message.answer(VALIDATION_MESSAGES["float"],
                                 reply_markup=campaign_back_keyboard(offset=offset, campaign_id=campaign_id))
            return
    elif full_param == "targeting":
        parts = new_value.split(',')
        if len(parts) != 4:
            await message.answer(VALIDATION_MESSAGES["targeting"],
                                 reply_markup=campaign_back_keyboard(offset=offset, campaign_id=campaign_id))
            return
        try:
            targeting = {
                "gender": parts[0].strip().upper(),
                "age_from": int(parts[1].strip()),
                "age_to": int(parts[2].strip()),
                "location": parts[3].strip()
            }
        except ValueError:
            await message.answer(VALIDATION_MESSAGES["targeting"],
                                 reply_markup=campaign_back_keyboard(offset=offset, campaign_id=campaign_id))
            return
        new_value = targeting

    update_data[full_param] = new_value

    user = await repo.get_user(user_id=message.from_user.id)
    if not user or not user.advertiser_id:
        await message.answer("❌ Ошибка: Рекламодатель не найден",
                             reply_markup=campaign_back_keyboard(offset=offset, campaign_id=campaign_id))
        await state.clear()
        return

    try:
        async with api_client as client:
            await client.update_campaign(
                advertiser_id=user.advertiser_id,
                campaign_id=campaign_id,
                data=CampaignUpdate.model_validate(update_data)
            )
            updated_campaign = await client.get_campaign(
                advertiser_id=user.advertiser_id,
                campaign_id=campaign_id
            )
    except Exception as e:
        print(traceback.format_exc())
        await message.answer("❌ Ошибка при обновлении кампании",
                             reply_markup=campaign_back_keyboard(offset=offset, campaign_id=campaign_id))
        await state.clear()
        return

    await message.answer(
        f"✅ Параметр <b>{get_param_name(full_param)}</b> успешно обновлён!"
    )

    await message.answer(
        format_campaign_message(updated_campaign),
        reply_markup=campaign_keyboard(offset, updated_campaign)
    )

    await state.clear()


@campaigns_router.message(CampaignEditState.waiting_for_new_value, F.photo)
async def process_campaign_edit_photo(message: Message, state: FSMContext, repo: Repo,
                                      api_client: AdvertisingPlatformClient):
    data = await state.get_data()
    campaign_id = data.get("campaign_id")
    offset = data.get("offset")

    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    downloaded_file = await message.bot.download_file(file_info.file_path)

    file_extension = os.path.splitext(file_info.file_path)[1].lstrip('.')

    file_key = await upload_cdn_fileobj(downloaded_file, file_extension)
    new_url = f"https://prodkekz.storage.yandexcloud.net/files/{file_key}"

    update_data = {"ad_photo_url": new_url}

    user = await repo.get_user(user_id=message.from_user.id)
    if not user or not user.advertiser_id:
        await message.answer("❌ Ошибка: Рекламодатель не найден",
                             reply_markup=campaign_back_keyboard(offset=offset, campaign_id=campaign_id))
        await state.clear()
        return

    try:
        async with api_client as client:
            await client.update_campaign(
                advertiser_id=user.advertiser_id,
                campaign_id=campaign_id,
                data=CampaignUpdate.model_validate(update_data)
            )
            updated_campaign = await client.get_campaign(
                advertiser_id=user.advertiser_id,
                campaign_id=campaign_id
            )
    except Exception as e:
        await message.answer("❌ Ошибка при обновлении кампании",
                             reply_markup=campaign_back_keyboard(offset=offset, campaign_id=campaign_id))
        await state.clear()
        return

    await message.answer("✅ Фотография успешно обновлена!")
    await message.answer(
        format_campaign_message(updated_campaign),
        reply_markup=campaign_keyboard(offset, updated_campaign)
    )
    await state.clear()


@campaigns_router.callback_query(CampaignStatsCallbackData.filter())
async def campaign_stats_handler(
        callback: CallbackQuery,
        callback_data: CampaignStatsCallbackData,
        repo: "Repo",
        state: "FSMContext",
        api_client: "AdvertisingPlatformClient"
):
    await callback.answer()
    campaign_id = callback_data.campaign_id
    offset = callback_data.offset

    user = await repo.get_user(user_id=callback.from_user.id)
    async with api_client as client:
        try:
            aggregated_stats = await client.get_campaign_stats(campaign_id)
            daily_stats = await client.get_campaign_daily_stats(campaign_id)
        except Exception as e:
            await callback.message.answer("Ошибка при получении статистики кампании")
            return

    stats_text = f"""
<b>📊 Статистика кампании</b>
ID: <code>{campaign_id}</code>

<b>Общая статистика:</b>
└ Показы: {aggregated_stats.impressions_count:,}
└ Кликов: {aggregated_stats.clicks_count:,}
└ Конверсия: {aggregated_stats.conversion:.2f}%
└ Расходы на показы: {aggregated_stats.spent_impressions:,.2f} ₽
└ Расходы на клики: {aggregated_stats.spent_clicks:,.2f} ₽
└ Общие затраты: {aggregated_stats.spent_total:,.2f} ₽
"""

    if daily_stats:
        days = [ds.date for ds in daily_stats]
        impressions = [ds.impressions_count for ds in daily_stats]
        clicks = [ds.clicks_count for ds in daily_stats]

        bar_width = 0.35
        index = np.arange(len(days))
        fig, ax = plt.subplots()
        ax.bar(index, impressions, bar_width, label='Показы')
        ax.bar(index + bar_width, clicks, bar_width, label='Клики')
        ax.set_xlabel('День')
        ax.set_ylabel('Количество')
        ax.set_title('Дневная статистика')
        ax.set_xticks(index + bar_width / 2)
        ax.set_xticklabels([str(day) for day in days])
        ax.legend()
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
    else:
        buf = None

    back_markup = campaign_back_keyboard(campaign_id, offset)

    if buf:
        buf_value = buf.getvalue()
        photo_input = BufferedInputFile(buf_value, filename="chart.png")
        await callback.message.answer_photo(
            photo=photo_input,
            caption=stats_text,
            parse_mode="HTML",
            reply_markup=back_markup
        )
    else:
        await callback.message.edit_text(
            text=stats_text,
            parse_mode="HTML",
            reply_markup=back_markup
        )
    await state.set_state(AuthState.waiting_for_uuid)