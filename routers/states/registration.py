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
    langs = State() # опционально
    verification = State()


class Client(StatesGroup):
    name = State()
    client_type = State()
    description = State()
    photo = State()
    confirm = State()

    # опционально (не требуется при первичной регистрации)
    links = State()
    langs = State()
    location = State()


