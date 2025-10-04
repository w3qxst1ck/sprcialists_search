from aiogram import Router
from routers.user import router as user_router

main_router = Router()

main_router.include_routers(
    user_router,
)
