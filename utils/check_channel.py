import logging

from aiogram import types, Bot
from aiogram.utils import exceptions

from loader import bot, db
from utils.language import LangSet


async def check_bot(user_id):
    myList = []
    bots = await db.select_all_bots()
    checking = False
    for x in bots:
        try:
            bot = Bot(token=x["bot_token"])
            title = await bot.get_me()
        except exceptions.ValidationError:
            logging.error("Token validation")
            continue
        except exceptions.Unauthorized:
            logging.error("Telegram unauthorized")
            continue
        try:
            status = await bot.get_chat(user_id)
            await bot.send_chat_action(user_id, types.ChatActions.TYPING)
        except Exception as e:
            logging.error(f"BOT USER HAS NO PERMISSION: {e}")
            myList.append(
                types.InlineKeyboardButton(
                    text=f"{title.full_name}", url=f"{x['bot_link']}"
                )
            )
            checking = True
    if checking:
        return myList
    else:
        return False


async def check_channel(user_id):
    keyboard = types.InlineKeyboardMarkup()
    channels = await db.select_all_channels()

    checking = False
    for i, channel in enumerate(channels, start=1):
        try:
            channell = await bot.get_chat(channel["channel_id"])
            _ = ["creator", "administrator", "member"]
            status = await bot.get_chat_member(channell.id, user_id)

        except Exception as e:
            continue

        if status.status in _:
            await db.delete_join_requests(
                user_id=int(user_id), chat_id=int(channell.id)
            )
            keyboard.add(
                types.InlineKeyboardButton(
                    text=f"✅ {i} - {await LangSet(user_id).get_translation('CHANNEL_NAME_MESSAGE')}",
                    url=f'{channel["channel_link"]}',
                )
            )

        else:
            check_join_requests = await db.select_join_requests(
                user_id=int(user_id), chat_id=int(channell.id)
            )
            if not check_join_requests:
                keyboard.add(
                    types.InlineKeyboardButton(
                        text=f"{i} - {await LangSet(user_id).get_translation('CHANNEL_NAME_MESSAGE')}",
                        url=f'{channel["channel_link"]}',
                    )
                )
                checking = True

    check_bots = await check_bot(user_id)
    if check_bots:
        checking = True
        keyboard.add(*check_bots)
    if checking:
        text = await LangSet(user_id).get_translation("sub_text")
        keyboard.row(
            types.InlineKeyboardButton(
                text=await LangSet(user_id).get_translation("channel_checker"),
                callback_data=f"check_channel",
            )
        )
        return text, keyboard
    else:
        return False
