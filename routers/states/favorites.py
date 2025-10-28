from aiogram.fsm.state import StatesGroup, State


class FavoriteExecutors(StatesGroup):
    feed = State()


class FavoriteOrders(StatesGroup):
    feed = State()
    contact = State()
    send_confirm = State()
