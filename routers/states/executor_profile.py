from aiogram.fsm.state import StatesGroup, State


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