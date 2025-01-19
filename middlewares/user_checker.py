import logging

from aiogram import types
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

from keyboards.inline.menu import language_keyboard
from libs.CheckLink import referral_checker
from loader import db, bot
from utils.check_channel import check_channel
from utils.language import LangSet


class UserCheckMiddleware(BaseMiddleware):

    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix="antiflood_"):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(UserCheckMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        chat_type = message.chat.type
        user_id = message.from_user.id
        if chat_type == types.ChatType.PRIVATE:
            # await bot.request('deleteChatMenuButton', {'user_id': user_id})
            try:
                await db.update_user_time(user_id=int(user_id))
            except Exception as err:
                logging.error(err)
            check_user = await db.select_user(user_id=int(user_id))
            if not check_user:
                try:
                    await referral_checker(message.text)
                except:
                    pass
                try:
                    await db.add_user(user_id=int(user_id))
                except Exception as err:
                    logging.error(err)
                # text = await LangSet(user_id)._('plase_select_lang')
                # await bot.send_message(user_id, text=text,
                #                        reply_markup=await language_keyboard(user_id))
                # raise CancelHandler()

            # if message.text != '/start' and message.text != "/admin":
            #     check = await db.select_settings()
            #     if check['value'] == 'True':
            #         check = await check_channel(message.from_user.id)
            #         if check:
            #             await message.delete()
            #             text, keyboard = check
            #             await message.answer(text=text,
            #                                  reply_markup=keyboard)
            #             raise CancelHandler()
        elif chat_type in (types.ChatType.SUPER_GROUP, types.ChatType.GROUP):
            check_user = await db.select_group(user_id=int(message.chat.id))
            if not check_user:
                try:
                    await db.add_group(user_id=int(message.chat.id))
                except Exception as err:
                    logging.error(err)
