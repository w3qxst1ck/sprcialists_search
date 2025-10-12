from aiogram import Router
from routers.user import router as user_router
from routers.start import router as start_router
from routers.profile import router as profile_router
from routers.executor_registration import router as ex_reg_router
from routers.client_registration import router as client_router

main_router = Router()

main_router.include_routers(
    user_router,
    start_router,
    profile_router,
    ex_reg_router,
    client_router,
)
