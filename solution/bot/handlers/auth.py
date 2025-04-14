import traceback
import uuid

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiohttp import ClientResponseError

from bot.database import Repo
from bot.keyboards import get_start_keyboard
from bot.keyboards.back import back_keyboard
from bot.states.auth import AuthState
from bot.utils.api_sdk import AdvertisingPlatformClient, AdvertiserUpsert

auth_router = Router()


@auth_router.callback_query(F.data == '/auth')
async def callback_auth(callback: CallbackQuery,
                        repo: Repo,
                        state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("🔑 Введите ваш UUID для входа в систему", reply_markup=back_keyboard())
    await state.set_state(AuthState.waiting_for_uuid)


@auth_router.callback_query(F.data == '/register')
async def callback_auth(callback: CallbackQuery,
                        repo: Repo,
                        state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("🔑 Введите ваш логин для регистрации в системе", reply_markup=back_keyboard())
    await state.set_state(AuthState.waiting_for_login)


@auth_router.callback_query(F.data == '/logout')
async def callback_auth(callback: CallbackQuery,
                        repo: Repo,
                        state: FSMContext):
    await callback.answer('Вы вышли из системы', show_alert=True)
    user = await repo.get_user(user_id=callback.from_user.id)
    user.advertiser_id = None
    user.advertiser_name = None
    await repo.session.commit()
    await callback.message.edit_text("""⚡️ <b>PROD ADS – инновационная рекламная платформа,
    которая изменит ваше представление о конверсиях раз и навсегда.</b>

    - Создавайте рекламные кампании.
    - Легко настраивайте таргетинг.
    - Получайте статистику по кампаниям.""",
                                     reply_markup=get_start_keyboard(user))


@auth_router.message(StateFilter(AuthState.waiting_for_uuid), F.text)
async def message_uuid_auth(message: Message, repo: Repo,
                            state: FSMContext, api_client: AdvertisingPlatformClient):
    uuid = message.text
    async with api_client as client:
        try:
            advertiser = await client.get_advertiser_by_id(uuid)
        except ClientResponseError as e:
            if e.status == 404:
                await message.answer(f"❌ Рекламодатель с UUID {uuid} не найден", reply_markup=back_keyboard())
                return
            elif e.status == 422:
                await message.answer(f"❌ Неверный UUID", reply_markup=back_keyboard())
                return
            await message.answer(f"❌ Ошибка", reply_markup=back_keyboard())
            return
        except Exception as e:
            print(traceback.format_exc(e))
            await message.answer(f"❌ Возникла неизвестная ошибка", reply_markup=back_keyboard())
            return
        else:
            user = await repo.get_user(user_id=message.from_user.id)
            print(advertiser)
            user.advertiser_id = advertiser.advertiser_id
            user.advertiser_name = advertiser.name
            await repo.session.commit()
            await message.answer(f"✅ Вы успешно вошли в систему как {advertiser.name}")
            await message.answer("""⚡️ <b>PROD ADS – инновационная рекламная платформа,
которая изменит ваше представление о конверсиях раз и навсегда.</b>

- Создавайте рекламные кампании.
- Легко настраивайте таргетинг.
- Получайте статистику по кампаниям.""",
                                 reply_markup=get_start_keyboard(user))

@auth_router.message(StateFilter(AuthState.waiting_for_login), F.text)
async def message_uuid_auth(message: Message, repo: Repo,
                            state: FSMContext, api_client: AdvertisingPlatformClient):
    name = message.text
    adv_id = str(uuid.uuid4())
    async with api_client as client:
        try:
            advertiser = await client.upsert_advertisers(advertisers=[AdvertiserUpsert(name=name,
                                                                                       advertiser_id=adv_id)])
        except Exception as e:
            print(traceback.format_exc())
            await message.answer(f"❌ Возникла неизвестная ошибка", reply_markup=back_keyboard())
            return
        else:
            user = await repo.get_user(user_id=message.from_user.id)
            print(advertiser)
            user.advertiser_id = adv_id
            user.advertiser_name = name
            await repo.session.commit()
            await message.answer(f"✅ Вы успешно вошли в систему как {advertiser.name}")
            await message.answer("""⚡️ <b>PROD ADS – инновационная рекламная платформа,
которая изменит ваше представление о конверсиях раз и навсегда.</b>

- Создавайте рекламные кампании.
- Легко настраивайте таргетинг.
- Получайте статистику по кампаниям.""",
                                 reply_markup=get_start_keyboard(user))
