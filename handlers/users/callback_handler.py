import logging

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler

from keyboards.inline.menu import add_keyboard, language_keyboard
from loader import dp, db, bot
from utils.check_channel import check_channel
from utils.language import LangSet


@dp.callback_query_handler(lambda call: call.data.startswith("language_"), state="*")
async def check_channel_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    id = call.data.replace("language_", "")
    await db.update_user_lang(lang=id, user_id=user_id)
    # await call.message.delete()
    text = await LangSet(user_id).get_translation("set_lang")
    emj = await LangSet(user_id).get_translation("emoji")
    bot_ = await bot.get_me()
    await call.answer(f"{emj} {text}")
    try:
        await call.message.edit_reply_markup(
            reply_markup=await language_keyboard(user_id)
        )
    except Exception as e:
        logging.error(e)


@dp.callback_query_handler(lambda call: call.data == "check_channel", state="*")
async def check_channel_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    check = await check_channel(user_id)
    bot_ = await bot.get_me()
    if check:
        text, keyboard = check
        text = await LangSet(user_id).get_translation("check_status")
        await call.answer(text, show_alert=True)
        try:
            await call.message.edit_reply_markup(reply_markup=keyboard)
        except Exception as e:
            await call.answer()
        raise CancelHandler()
    else:
        await call.message.delete()
        try:
            text = await LangSet(user_id).get_translation("start")
            await call.message.edit_text(
                text.format(bot_.username), reply_markup=await add_keyboard(user_id)
            )
        except Exception as err:
            logging.error(err)
            text = await LangSet(user_id).get_translation("start")
            await call.message.answer(
                text.format(bot_.username), reply_markup=await add_keyboard(user_id)
            )
