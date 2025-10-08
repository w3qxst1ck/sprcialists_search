from aiogram import Router
from routers.user import router as user_router
from routers.start import router as start_router

main_router = Router()

main_router.include_routers(
    user_router,
    start_router
)
