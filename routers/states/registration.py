from aiogram.fsm.state import StatesGroup, State


class Executor(StatesGroup):
    name = State()
    age = State()
    profession = State()
    jobs = State()
    description = State()
    rate = State()
    experience = State()
    links = State()
    availability = State()
    contacts = State()
    location = State()
    tags = State()
    verification = State

    user: Mapped["User"] = relationship(back_populates="executor_profile")
