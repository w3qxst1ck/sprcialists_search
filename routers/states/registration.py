from aiogram.fsm.state import StatesGroup, State


class Executor(StatesGroup):
    name = State()
    age = State()
    profession = State()
    # TODO сделать аватар
    # photo = State()
    jobs = State()
    description = State()
    rate = State()
    experience = State()
    links = State()
    contacts = State()
    location = State()
    tags = State()
    langs = State()
    verification = State()


class Client(StatesGroup):
    name = State()
    description = State()
    client_type = State()


