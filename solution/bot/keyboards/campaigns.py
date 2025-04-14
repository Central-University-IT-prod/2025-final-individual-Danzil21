import math
from typing import List

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.pagination.page_factory import page_factory
from bot.utils.api_sdk import CampaignResponse


class CampaignPageCallbackData(CallbackData, prefix="/campaigns/page"):
    offset: int = 0


class CampaignCallbackData(CallbackData, prefix="/campaigns/info"):
    campaign_id: str
    offset: int

class CampaignEditCallbackData(CallbackData, prefix="CED"):
    campaign_id: str
    p: str
    off: int

class CampaignStatsCallbackData(CallbackData, prefix="/campaigns/stats"):
    campaign_id: str
    offset: int

PARAM_SHORT_MAP = {
    "impressions_limit": "IL",
    "clicks_limit": "CL",
    "cost_per_impression": "CPI",
    "cost_per_click": "CPC",
    "ad_title": "AT",
    "ad_text": "AD",
    "ad_photo_url": "AP",
    "start_date": "SD",
    "end_date": "ED",
    "targeting": "T"
}

def get_navigation_keyboard(current_page: int, total_campaigns: int,
                            campaigns: List[CampaignResponse]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    max_page = math.ceil(total_campaigns / 10) - 1

    for campaign in campaigns:
        builder.row(
            InlineKeyboardButton(text=campaign.ad_title,
                                 callback_data=CampaignCallbackData(campaign_id=campaign.campaign_id, offset=current_page).pack())
        )

    if max_page > 0:
        pagination_buttons = page_factory(current_page, max_page, CampaignPageCallbackData)
        builder.row(*pagination_buttons, width=5)

    builder.row(
        InlineKeyboardButton(text="« Назад",
                             callback_data="/start")
    )
    return builder.as_markup()




def campaign_keyboard(offset: int, campaign) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    cid_full = str(campaign.campaign_id)
    builder.row(
        InlineKeyboardButton(
            text="📊 Статистика",
            callback_data=CampaignStatsCallbackData(
                campaign_id=cid_full, offset=offset
            ).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Изменить лимит показов",
            callback_data=CampaignEditCallbackData(
                campaign_id=cid_full, p=PARAM_SHORT_MAP["impressions_limit"], off=offset
            ).pack()
        ),
        InlineKeyboardButton(
            text="Изменить лимит кликов",
            callback_data=CampaignEditCallbackData(
                campaign_id=cid_full, p=PARAM_SHORT_MAP["clicks_limit"], off=offset
            ).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Изменить цену за показ",
            callback_data=CampaignEditCallbackData(
                campaign_id=cid_full, p=PARAM_SHORT_MAP["cost_per_impression"], off=offset
            ).pack()
        ),
        InlineKeyboardButton(
            text="Изменить цену за клик",
            callback_data=CampaignEditCallbackData(
                campaign_id=cid_full, p=PARAM_SHORT_MAP["cost_per_click"], off=offset
            ).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Изменить заголовок",
            callback_data=CampaignEditCallbackData(
                campaign_id=cid_full, p=PARAM_SHORT_MAP["ad_title"], off=offset
            ).pack()
        ),
        InlineKeyboardButton(
            text="Изменить текст",
            callback_data=CampaignEditCallbackData(
                campaign_id=cid_full, p=PARAM_SHORT_MAP["ad_text"], off=offset
            ).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Изменить фото",
            callback_data=CampaignEditCallbackData(
                campaign_id=cid_full, p=PARAM_SHORT_MAP["ad_photo_url"], off=offset
            ).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Изменить дату начала",
            callback_data=CampaignEditCallbackData(
                campaign_id=cid_full, p=PARAM_SHORT_MAP["start_date"], off=offset
            ).pack()
        ),
        InlineKeyboardButton(
            text="Изменить дату окончания",
            callback_data=CampaignEditCallbackData(
                campaign_id=cid_full, p=PARAM_SHORT_MAP["end_date"], off=offset
            ).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Изменить таргетинг",
            callback_data=CampaignEditCallbackData(
                campaign_id=cid_full, p=PARAM_SHORT_MAP["targeting"], off=offset
            ).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data=CampaignPageCallbackData(offset=offset).pack()
        )
    )
    return builder.as_markup()