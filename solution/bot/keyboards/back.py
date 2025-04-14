from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.campaigns import CampaignCallbackData


def back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="« Назад",
                             callback_data="/start")
    )
    return builder.as_markup()


def campaign_back_keyboard(campaign_id, offset: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    back_button = InlineKeyboardButton(
        text="« Назад",
        callback_data=CampaignCallbackData(offset=offset, campaign_id=campaign_id).pack()
    )
    builder.row(back_button)
    return builder.as_markup()