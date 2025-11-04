from typing import Any

from database.orm import AsyncOrm
from schemas.executor import Executor


async def check_verified_executor(tg_id: str, session: Any) -> bool:
    """Проверка верифицирован ли исполнитель"""
    executor: Executor = await AsyncOrm.get_executor_by_tg_id(tg_id, session)

    return executor.verified