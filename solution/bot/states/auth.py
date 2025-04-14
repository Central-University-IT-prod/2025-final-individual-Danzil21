from aiogram.filters.state import State, StatesGroup

class AuthState(StatesGroup):
    waiting_for_uuid = State()
    waiting_for_json = State()
    waiting_for_login = State()
