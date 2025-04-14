from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.database.models import BotUser
from bot.keyboards.campaigns import CampaignPageCallbackData


def get_start_keyboard(user: BotUser) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if user.advertiser_id is not None:
        builder.row(InlineKeyboardButton(text="🪙 Рекламные кампании", callback_data=CampaignPageCallbackData(offset=0).pack()))
        builder.row(InlineKeyboardButton(text="➕ Новая кампания", callback_data="/campaigns/create"))
        builder.row(InlineKeyboardButton(text="📊 Общая статистика", callback_data="/summary_stat"))
        builder.row(InlineKeyboardButton(text="🚫 Выйти ({})".format(user.advertiser_name), callback_data="/logout"))
    else:
        builder.row(InlineKeyboardButton(text="🔐 Войти", callback_data="/auth"))
        builder.row(InlineKeyboardButton(text="🔏 Зарегистрироваться", callback_data="/register"))
    return builder.as_markup()


def get_start_reply_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Меню"))
    return builder.as_markup(resize_keyboard=True)
