import logging

from aiogram import Dispatcher

from libs.AdminsList import admins_list


async def on_startup_notify(dp: Dispatcher):
    for admin in await admins_list():
        try:
            await dp.bot.send_message(admin, "Bot ishga tushdi")

        except Exception as err:
            logging.exception(err)
