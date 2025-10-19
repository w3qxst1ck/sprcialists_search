from aiogram.fsm.state import StatesGroup, State


class FavoriteExecutors(StatesGroup):
    feed = State()