from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.database import Repo
from bot.keyboards import get_start_keyboard
from bot.keyboards.start import get_start_reply_keyboard

start_router = Router()


@start_router.message(Command("start"))
@start_router.message(F.text == "Меню")
async def message_start(message: Message,
                        repo: Repo,
                        state: FSMContext):
    await state.clear()
    from_user = message.from_user
    user = await repo.get_user(user_id=from_user.id)
    if not user:
        try:
            await repo.create_user(user_id=from_user.id)
        except:
            pass

    await message.answer_sticker(sticker='CAACAgIAAxkBAAECF6xnuMhe7PFbvdAQCHo5bDi0R4trSwACyUQAAgdYmEpkiMeKFtiXYzYE',
                                 reply_markup=get_start_reply_keyboard())
    await message.answer("""⚡️ <b>PROD ADS – инновационная рекламная платформа,
которая изменит ваше представление о конверсиях раз и навсегда.</b>

- Создавайте рекламные кампании.
- Легко настраивайте таргетинг.
- Получайте статистику по кампаниям.""",
                         reply_markup=get_start_keyboard(user))


@start_router.callback_query(F.data == '/start')
async def callback_start(callback: CallbackQuery,
                         repo: Repo):
    await callback.answer()
    user = await repo.get_user(user_id=callback.from_user.id)
    await callback.message.edit_text("""⚡️ <b>PROD ADS – инновационная рекламная платформа,
которая изменит ваше представление о конверсиях раз и навсегда.</b>

- Создавайте рекламные кампании.
- Легко настраивайте таргетинг.
- Получайте статистику по кампаниям.""",
                                     reply_markup=get_start_keyboard(user))
