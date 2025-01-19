from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart

from keyboards.inline.menu import language_keyboard, add_keyboard
from libs.CheckLink import referral_checker, media_checker, ads_checker
from loader import dp, bot
from utils.language import LangSet


# @dp.message_handler()
async def start(message: types.Message):
    print(message.html_text)


@dp.message_handler(CommandStart(), state="*")
async def bot_start_handler(message: types.Message):
    bot_ = await bot.get_me()
    if message.chat.type == "private":
        user_id = message.from_user.id
        await media_checker(message.text, user_id)
        text = await LangSet(user_id).get_translation("start")
        await message.answer(
            text.format(bot_.username), reply_markup=await add_keyboard(user_id)
        )
        try:
            await ads_checker(user_id)
        except:
            pass
    elif message.chat.type == "supergroup" or message.chat.type == "group":
        user_id = message.chat.id
        text = await LangSet(user_id).get_translation("start")
        await message.answer(
            text.format(bot_.username), reply_markup=await add_keyboard(user_id)
        )


@dp.message_handler(commands=["lang"], state="*")
async def bot_lang_handler(message: types.Message):
    user_id = message.from_user.id
    text = await LangSet(user_id).get_translation("plase_select_lang")
    await bot.send_message(
        user_id, text=text, reply_markup=await language_keyboard(user_id)
    )
