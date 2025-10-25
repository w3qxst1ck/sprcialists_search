from aiogram import Router
from routers.start import router as start_router
from routers.executor_registration import router as ex_reg_router
from routers.client_registration import router as client_reg_router
from routers.admin import private_router as admin_private_router
from routers.admin_group import group_router as admin_group_router
from routers.menu import router as main_menu_router
from routers.find_executor import router as find_executor_router
from routers.orders import router as orders_router
from routers.favorites_executors import router as favorites_executors_router
from routers.favorites_orders import router as favorites_orders_router
from routers.executor_profile import router as executor_profile_router
from routers.find_order import router as find_order_router

main_router = Router()

main_router.include_routers(
    start_router,
    ex_reg_router,
    client_reg_router,
    admin_private_router,
    admin_group_router,
    main_menu_router,
    find_executor_router,
    find_order_router,
    orders_router,
    favorites_executors_router,
    favorites_orders_router,
    executor_profile_router,
)
