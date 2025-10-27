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


class EditOrderProfession(StatesGroup):
    profession = State()
    jobs = State()


class EditOrderTitle(StatesGroup):
    title = State()


class EditOrderTask(StatesGroup):
    task = State()


class EditOrderPrice(StatesGroup):
    price = State()


class EditOrderDeadline(StatesGroup):
    deadline = State()


class EditOrderRequirements(StatesGroup):
    requirements = State()


class EditOrderFiles(StatesGroup):
    files = State()
