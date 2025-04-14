from aiogram.filters.state import StatesGroup, State

class CampaignEditState(StatesGroup):
    waiting_for_new_value = State()
