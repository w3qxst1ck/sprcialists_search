from aiogram.fsm.state import StatesGroup, State


class CreateOrder(StatesGroup):
    profession = State()
    jobs = State()
    title = State()
    task = State()
    price = State()
    deadline = State()
    requirements = State()
    files = State()
    confirmation = State()
