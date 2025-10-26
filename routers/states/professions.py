from aiogram.fsm.state import StatesGroup, State


class AddProfession(StatesGroup):
    title = State()
    emoji = State()
    confirmation = State()