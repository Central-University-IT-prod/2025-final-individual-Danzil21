from aiogram.filters.state import State, StatesGroup


class CreateCollectionState(StatesGroup):
    waiting_for_name = State()
    waiting_for_links = State()

class CreateTrackingState(StatesGroup):
    waiting_for_name = State()
    waiting_for_keyword = State()

class EditTrackingState(StatesGroup):
    waiting_for_name = State()
    waiting_for_keyword = State()


class PictureAnalyticsState(StatesGroup):
    waiting_for_links = State()


class CpmCostState(StatesGroup):
    waiting_for_digit = State()
