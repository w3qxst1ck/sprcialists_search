import random

from schemas.executor import ExecutorShow


def shuffle_executors(executors: list[ExecutorShow]) -> list[ExecutorShow]:
    """Перемешивание списка исполнителей"""
    return random.sample(executors, len(executors))
