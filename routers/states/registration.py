from aiogram.fsm.state import StatesGroup, State


class Executor(StatesGroup):
    name = State()
    photo = State()
    age = State()
    profession = State()
    jobs = State()
    description = State()
    rate = State() # опционально
    experience = State()
    links = State()
    contacts = State() # опционально
    location = State() # опционально
    tags = State() # убрать
    langs = State() # опционально
    verification = State()


class Client(StatesGroup):
    name = State()
    description = State()
    client_type = State()
    links = State()
    langs = State()
    location = State()
    photo = State()

