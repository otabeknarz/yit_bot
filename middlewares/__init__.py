from aiogram import Dispatcher

from loader import dp
from .throttling import ThrottlingMiddleware
from .user_checker import UserCheckMiddleware

if __name__ == "middlewares":
    dp.middleware.setup(ThrottlingMiddleware())
    dp.middleware.setup(UserCheckMiddleware())
