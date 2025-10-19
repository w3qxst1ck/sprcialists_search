import random

from schemas.executor import Executor


def shuffle_executors(executors: list[Executor]) -> list[Executor]:
    """Перемешивание списка исполнителей"""
    return random.sample(executors, len(executors))
