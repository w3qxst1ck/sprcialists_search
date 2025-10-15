from aiogram.fsm.state import StatesGroup, State


class SelectJobs(StatesGroup):
    jobs = State()