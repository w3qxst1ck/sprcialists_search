from aiogram.fsm.state import StatesGroup, State


class CreateOrder(StatesGroup):
    profession = State()
    title = State()
    task = State()
    price = State()
    deadline = State()