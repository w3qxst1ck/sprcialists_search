from aiogram import Router
from routers.start import router as start_router
from routers.profile import router as profile_router
from routers.executor_registration import router as ex_reg_router
from routers.client_registration import router as client_reg_router
from routers.admin import private_router as admin_private_router
from routers.admin_group import group_router as admin_group_router
from routers.menu import router as main_menu_router
from routers.find_executor import router as find_executor_router

main_router = Router()

main_router.include_routers(
    start_router,
    profile_router,
    ex_reg_router,
    client_reg_router,
    admin_private_router,
    admin_group_router,
    main_menu_router,
    find_executor_router
)
