from aiogram.fsm.state import StatesGroup, State


class EditExecutor(StatesGroup):
    view = State()
    photo = State()
    profession = State()
    jobs = State()
    rate = State()
    experience = State()
    description = State()
    contacts = State()
    location = State()
    links = State()

class EditPhoto(StatesGroup):
    photo = State()


class EditProfession(StatesGroup):
    profession = State()
    jobs = State()


class EditRate(StatesGroup):
    rate = State()


class EditExperience(StatesGroup):
    experience = State()


class EditDescription(StatesGroup):
    description = State()


class EditContacts(StatesGroup):
    contacts = State()


class EditLocation(StatesGroup):
    location = State()


class EditLinks(StatesGroup):
    links = State()