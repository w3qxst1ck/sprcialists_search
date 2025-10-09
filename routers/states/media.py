from aiogram.fsm.state import StatesGroup, State


class LoadMedia(StatesGroup):
    photo = State()