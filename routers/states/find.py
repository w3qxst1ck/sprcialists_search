from aiogram.fsm.state import StatesGroup, State


class SelectJobs(StatesGroup):
    jobs = State()


class ExecutorsFeed(StatesGroup):
    show = State()


class OrdersFeed(StatesGroup):
    show = State()