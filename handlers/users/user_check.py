import logging

from aiogram import types

from keyboards.inline.menu import add_keyboard
from loader import dp, db, bot
from utils.language import LangSet


# @dp.my_chat_member_handler()
# async def check_user_handler(message: types.ChatMemberUpdated):
#     print(message)
#     if message.chat.type == "private":
#         status = message.new_chat_member.status
#         user_id = message.from_user.id
#         if status == "member":
#             await db.update_user_status(status="active", user_id=user_id)
#         elif status == "kicked":
#             await db.update_user_status(status="passive", user_id=user_id)
#         else:
#             await db.update_user_status(status="active", user_id=user_id)
#     elif message.chat.type in ["group", "supergroup"]:
#         status = message.new_chat_member.status
#         user_id = message.chat.id
#         check_user = await db.select_group(user_id=int(message.chat.id))
#         if not check_user:
#             try:
#                 await db.add_group(user_id=int(message.chat.id))
#             except Exception as err:
#                 logging.error(err)
#         if status == "member":
#             await db.update_mailling_table_status(
#                 table="groups", status="active", user_id=user_id
#             )
#             bot_ = await bot.get_me()
#             text = await LangSet(user_id)._("start")
#             await bot.send_message(
#                 chat_id=user_id,
#                 text=text.format(bot_.username),
#                 reply_markup=await add_keyboard(user_id),
#             )
#         elif status == "kicked":
#             await db.update_mailling_table_status(
#                 table="groups", status="passive", user_id=user_id
#             )
#         elif status == "left":
#             await db.update_mailling_table_status(
#                 table="groups", status="passive", user_id=user_id
#             )
#         else:
#             await db.update_mailling_table_status(
#                 table="groups", status="active", user_id=user_id
#             )
#             bot_ = await bot.get_me()
#             text = await LangSet(user_id)._("start")
#             await bot.send_message(
#                 chat_id=user_id,
#                 text=text.format(bot_.username),
#                 reply_markup=await add_keyboard(user_id),
#             )
