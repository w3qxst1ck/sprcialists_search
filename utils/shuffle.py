import random

from schemas.executor import Executor
from schemas.order import Order


def shuffle_executors(executors: list[Executor]) -> list[Executor]:
    """Перемешивание списка исполнителей"""
    return random.sample(executors, len(executors))


def shuffle_orders(orders: list[Order]) -> list[Order]:
    """Перемешивание списка заказов"""
    return random.sample(orders, len(orders))
