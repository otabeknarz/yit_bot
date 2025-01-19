import logging

from aiogram import types

from loader import dp, db


# @dp.chat_join_request_handler()
# async def join_request_handler(message):
#     chat = message.chat
#     user = message.from_user
#     logging.info("Joining request for user %s", user.first_name)
#     check_user = await db.select_join_requests(user_id=user.id, chat_id=chat.id)
#     if not check_user:
#         await db.add_join_requests(user_id=user.id, chat_id=chat.id)
#
#
# @dp.chat_member_handler()
# async def chat_m_handler(message):
#     old = message.old_chat_member
#     new = message.new_chat_member
#     if new.status == "member":
#         await db.delete_join_requests(
#             user_id=message.from_user.id, chat_id=message.chat.id
#         )
#     if new.status == "left":
#         await db.delete_join_requests(
#             user_id=message.from_user.id, chat_id=message.chat.id
#         )
