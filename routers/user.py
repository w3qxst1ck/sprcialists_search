from aiogram import Router, types
from aiogram.filters import Command
from database.orm import AsyncOrm

from logger import logger
from schemas.user import UserAdd

router = Router()


@router.message(Command(f"start"))
async def start(message: types.Message, session: any) -> None:
    """Стартовый роутер"""
    user = UserAdd(
        tg_id=str(message.from_user.id),
        username=message.from_user.username,
        firstname=message.from_user.first_name,
        lastname=message.from_user.last_name
    )
    await AsyncOrm.create_user(user, session)
    logger.info("Created user")
    await message.answer(message.text)