import asyncio
import json
import logging
import os
from datetime import datetime

from aiogram import types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import (
    InputMediaDocument,
    InputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils import exceptions

from data.config import DATABASE_INFO, MESSAGE_SENDER_COMMAND
from handlers.admins.key import adminKeyboard
from libs.create_link import generate_custom_uuid
from libs.download_music import get_top_musics
from loader import dp, db, bot


async def bot_checker(bot_token, bot_user) -> dict:
    try:
        new_bot = Bot(token=bot_token)
    except exceptions.ValidationError:
        logging.error("Token validation")
        return dict(status=False, message="<b>Bot tokeni yaroqsiz.</b>")
    try:
        bot_ = await new_bot.get_me()
    except exceptions.Unauthorized:
        logging.error("Telegram unauthorized")
        return dict(status=False, message="<b>Bot tokeni yaroqsiz.</b>")
    if bot_.username.lower() != bot_user.lower():
        logging.error("Invalid username")
        return dict(status=False, message="<b>Bot usernamesi yaroqsiz.</b>")

    return dict(status=True, message="Bot successfully")


@dp.message_handler(
    Command(commands=["admin", "panel"], prefixes="./!"), is_owner=True, state="*"
)
async def admin_menu_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("ADMIN PANEL", reply_markup=adminKeyboard.menu())


@dp.callback_query_handler(text="panel", is_owner=True, state="*")
async def stat_handler(message: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        await message.message.edit_text("BOSH MENU", reply_markup=adminKeyboard.menu())
    except Exception as e:
        logging.error(e)
        await message.message.delete()
        await message.message.answer("ADMIN PANEL", reply_markup=adminKeyboard.menu())


@dp.callback_query_handler(text="close", is_owner=True, state="*")
async def stat_handler(message: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await message.message.delete()


@dp.callback_query_handler(text="stat", is_owner=True, state="*")
async def stat_handler(message: types.CallbackQuery, state: FSMContext):
    res = await db.count_all_users()
    all, active, daily, weekly, monthly, uniqueUser = (
        res["all"],
        res["active"],
        res["daily_users"],
        res["weekly_users"],
        res["monthly_users"],
        res["unique_users"],
    )
    date_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    text = f"""<b>🧑🏻‍💻 Botdagi obunachilar: <code>{all}</code> ta (+ {daily})

Faol obunachilar: <code>{active}</code> ta 
Oxirgi 1 haftada: <code>{weekly}</code> ta obunachi qo'shildi
Oxirgi 1 oyda: <code>{monthly}</code> ta obunachi qo'shildi

Unique Users: {uniqueUser}</b>
"""
    res = await db.count_all_groups()
    all, active, daily, weekly, monthly = (
        res["all"],
        res["active"],
        res["daily_users"],
        res["weekly_users"],
        res["monthly_users"],
    )
    res1 = await db.count_all_content()
    audio, media, daily_media, daily_audio = (
        res1["audio"],
        res1["media"],
        res1["daily_media"],
        res1["daily_audio"],
    )
    text += f"""
<b>Faol Guruhlar: <code>{active}</code> ta (+ {daily})
Oxirgi 1 haftada: <code>{weekly}</code> ta guruh qo'shildi
Oxirgi 1 oyda: <code>{monthly}</code> ta guruh qo'shildi</b>

<i>Audio yuklamalar - {audio} (+{daily_audio})
Media yuklamalar - {media} (+{daily_media})
Jami - {media + audio} (+{daily_media + daily_audio})</i>

"""

    for key, value in dict(await db.count_language_users()).items():
        text += f"<b>{key}: {value}</b>\n"
    text += f"\n<b>📅 {date_time}</b>"
    await message.answer()
    await message.message.edit_text(text, reply_markup=adminKeyboard.back_panel())


# Todo: Channels settings
@dp.callback_query_handler(text="channels", is_owner=True, state="*")
async def channels_settings_handler(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.answer()
    await call.message.edit_text(
        "KANALLAR SOZLAMALARI", reply_markup=await adminKeyboard.channel_settings()
    )


@dp.callback_query_handler(text="channels_on_off", is_owner=True, state="*")
async def channels_on_of_handler(call: types.CallbackQuery):
    status = await db.select_settings()
    if status["value"] == "True":
        text = "❌ Majburiy a'zolik | O'chirildi"
        await db.update_settings_status(id=status["id"], value="False")
    else:
        text = "✅ Majburiy a'zolik | Yoqildi"
        await db.update_settings_status(id=status["id"], value="True")

    await call.answer(text, show_alert=True)
    try:
        await call.message.edit_reply_markup(
            reply_markup=await adminKeyboard.channel_settings()
        )
    except Exception as err:
        logging.error(err)
        await call.message.delete()
        await call.message.answer(
            "KANAL SOZLAMALARI", reply_markup=await adminKeyboard.channel_settings()
        )


@dp.callback_query_handler(text="channels_list", is_owner=True, state="*")
async def channels_list_handler(call: types.CallbackQuery):
    result = await adminKeyboard.channels_list()
    if result:
        await call.message.edit_text("KANALLAR", reply_markup=result)
    else:
        await call.answer("Kanallar mavjud emas!", show_alert=True)


@dp.callback_query_handler(
    lambda c: c.data.startswith("channel_"), is_owner=True, state="*"
)
async def select_channel_handler(call: types.CallbackQuery):
    await call.answer()
    channel_id = call.data.split("_")[1]
    try:
        channel = await bot.get_chat(channel_id)
        count = await bot.get_chat_member_count(channel_id)
        if count > 1000:
            count = f"{round(count / 1000, 1)}K"
    except Exception as err:
        logging.error(err)
        await call.answer("Kanal topilmadi", show_alert=True)
        return
    text = "<b>"
    text += f"Kanal: {channel.title}\n"
    text += f"Kanal ID: {channel.id}\n"
    text += f"Kanal linki: {channel.invite_link}\n"
    text += f"Kanalga a'zo: {count}\n"
    text += "</b>"
    await call.message.edit_text(
        text=text,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="channels_list")
        ),
        disable_web_page_preview=True,
    )


@dp.callback_query_handler(
    lambda c: c.data == "delete_channel", is_owner=True, state="*"
)
async def delete_channel_handler(call: types.CallbackQuery):
    result = await adminKeyboard.delete_channels()
    if not result:
        await call.answer("Kanallar mavjud emas!", show_alert=True)
        return
    await call.answer()
    await call.message.edit_text("O'chirish uchun kanalni tanlang", reply_markup=result)


@dp.callback_query_handler(
    lambda c: c.data.startswith("delete_channel_"), is_owner=True, state="*"
)
async def delete_channel_handler(call: types.CallbackQuery):
    channel_id = call.data.replace("delete_channel_", "")
    await db.delete_channel(channel_id=channel_id)
    await call.message.edit_text(
        "KANAL OCHIRILDI!", reply_markup=await adminKeyboard.channel_settings()
    )


class FromChannel(StatesGroup):
    channel_id = State()
    channel_link = State()


@dp.callback_query_handler(text="force_settings", state="*", is_owner=True)
async def force_settings_handler(call: types.CallbackQuery):
    await call.message.edit_text(
        "<b>Kerakli bo'limni tanlang:</b>",
        reply_markup=await adminKeyboard.force_settings(),
    )


@dp.callback_query_handler(text="bots", state="*", is_owner=True)
async def bots_handler(call: types.CallbackQuery):
    await call.message.edit_text(
        "<b>Kerakli bo'limni tanlang:</b>",
        reply_markup=await adminKeyboard.bots_keyboard(),
    )


@dp.callback_query_handler(text="bot_add", state="*", is_owner=True)
async def bot_add_handler(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    bot_ = await bot.get_me()
    await call.message.edit_text(
        f"<b>1. Birinchi bo‘lib botni({bot_.username}) usernamesini yuboring!</b>",
        reply_markup=adminKeyboard.back_panel(),
    )
    await state.set_state("FormBot.username")


@dp.message_handler(state="FormBot.username", content_types=["text"], is_owner=True)
async def bot_user(message: types.Message, state: FSMContext):
    await state.update_data(bot_user=message.text)
    await message.answer(
        "Endi bot tokenini kiriting: ", reply_markup=adminKeyboard.back_panel()
    )
    await state.set_state("FormBot.bot_token")


@dp.message_handler(state="FormBot.bot_token", content_types=["text"], is_owner=True)
async def bot_user(message: types.Message, state: FSMContext):
    info = await state.get_data()
    result = await bot_checker(bot_token=message.text, bot_user=info["bot_user"])
    if result["status"]:
        await state.update_data(bot_token=message.text)
        await message.answer(
            "Endi bot linkini kiriting: ", reply_markup=adminKeyboard.back_panel()
        )
        await state.set_state("FormBot.bot_link")
    else:
        await message.answer(
            "Qandaydir xatolik yuz berdi keyinroq qayta urinb ko'ring!",
            reply_markup=adminKeyboard.back_panel(),
        )
        await state.finish()


@dp.message_handler(state="FormBot.bot_link", content_types=["text"], is_owner=True)
async def bot_user(message: types.Message, state: FSMContext):
    info = await state.get_data()
    bot_user = info["bot_user"]
    bot_token = info["bot_token"]
    bot_link = message.text
    result = await db.select_bot(bot_token=str(bot_token))
    if result:
        await message.answer(
            f"<b>Bot avval qo'shilgan:</b> @{bot_user}",
            reply_markup=await adminKeyboard.force_settings(),
        )
    else:
        await message.answer(
            f"<b>@{bot_user} Muvaffaqiyatli qo'shildi ✅</b>",
            reply_markup=adminKeyboard.back_panel(),
        )
        await db.add_bot(bot_token=bot_token, bot_link=bot_link)
    await state.finish()


@dp.callback_query_handler(text="bots_list", is_owner=True, state="*")
async def channels_list_handler(call: types.CallbackQuery):
    result = await adminKeyboard.bots_list()
    if result:
        await call.message.edit_text("Botlar", reply_markup=result)
    else:
        await call.answer("botlar mavjud emas!", show_alert=True)


@dp.callback_query_handler(text="delbot", is_owner=True, state="*")
async def channels_list_handler(call: types.CallbackQuery):
    result = await adminKeyboard.delete_bots()
    if result:
        await call.message.edit_text(
            "Ochirmoqchi bolgan botingiz ustiga 1marta bosing", reply_markup=result
        )
    else:
        await call.answer("botlar mavjud emas!", show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith("dd_"), is_owner=True, state="*")
async def delete_channel_handler(call: types.CallbackQuery):
    channel_id = call.data.replace("dd_", "")
    await db.delete_bot(id=int(channel_id))
    await call.message.edit_text(
        "BOT OCHIRILDI!", reply_markup=await adminKeyboard.bots_keyboard()
    )


@dp.callback_query_handler(text="add_channel", is_owner=True, state="*")
async def add_channel_handler(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    bot_ = await bot.get_me()
    await call.message.edit_text(
        f"<b>1. Birinchi bo‘lib botni(@{bot_.username})"
        f" kanalingizda administrator qiling.\n\n"
        f"2. Administrator qilganingizdan keyn esa kanalingizni"
        f" Public link (@channel)manzilini yoki kanal ID raqamini yuboring (-10012334465)"
        f" yoki kanalingizdan biror bir postni Forward from formatida yuboring</b>",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="channels")
        ),
    )
    await FromChannel.channel_id.set()


@dp.message_handler(
    is_owner=True, state=FromChannel.channel_id, content_types=types.ContentType.ANY
)
async def channel_id_handler(message: types.Message, state: FSMContext):
    channel_id = None
    channelid = message.text
    if message.forward_from_chat:
        channel_id = str(message.forward_from_chat.id)
    elif channelid.startswith("@"):
        channel_id = str(channelid)
    elif channelid.startswith("-100"):
        channel_id = str(channelid)
    elif channelid.isdigit():
        if not channelid.startswith("-100"):
            channel_id = f"-100{channelid}"
    try:
        channel = await bot.get_chat(channel_id)
        _ = ["creator", "administrator"]
        status = await bot.get_chat_member(channel.id, message.from_user.id)
        if not status.status in _:
            await message.answer(
                text="Kanal topilmadi",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="channels")
                ),
            )
            return
        channel_id = channel.id
        channel_title = channel.title
        channel_link = await channel.export_invite_link()
    except Exception as e:
        logging.error(e)
        await message.answer(
            text="Kanal topilmadi",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="channels")
            ),
        )
        return
    result = await db.select_channels(channel_id=str(channel_id))
    if not result:
        await message.answer(text="Yaxshi endi kanal linkni yuboring!")
        await state.update_data(id=channel.id)
        await FromChannel.channel_link.set()
    else:
        await message.answer(
            '<b>Kanal avval qo\'shilgan:</b> <a href="{}">{}</a>'.format(
                channel_link, channel_title
            ),
            parse_mode="html",
            reply_markup=await adminKeyboard.channel_settings(),
        )
        await state.finish()


@dp.message_handler(is_owner=True, state=FromChannel.channel_link)
async def channel_link_handler(message: types.Message, state: FSMContext):
    info = await state.get_data()
    channel_id = info["id"]
    try:
        channel = await bot.get_chat(channel_id)
        _ = ["creator", "administrator"]
        status = await bot.get_chat_member(channel.id, message.from_user.id)
        if not status.status in _:
            await message.answer(
                text="Kanal topilmadi",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="channels")
                ),
            )
            return
        channel_id = channel.id
        channel_title = channel.title
        channel_link = await channel.export_invite_link()
    except Exception as e:
        logging.error(e)
        await message.answer(
            text="Kanal topilmadi",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="channels")
            ),
        )
        return

    result = await db.add_channel(channel_id=str(channel_id), channel_link=message.text)
    if result:
        await message.answer(
            '<b>Kanal qo\'shildi:</b> <a href="{}">{}</a>'.format(
                channel_link, channel_title
            ),
            parse_mode="html",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="channels")
            ),
        )
        await state.finish()
    else:
        await message.answer(
            text="Qandaydir xatolik yuz berdi keyinroq qayta urinb ko'ring!",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="channels")
            ),
        )
        await state.finish()


@dp.callback_query_handler(
    state="*",
    text="ads_bolum",
    is_owner=True,
)
async def ads_bolum_handler(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "Kerakli bolimni tanlang:", reply_markup=await adminKeyboard.ads_settings()
    )


@dp.callback_query_handler(
    state="*",
    text="add_ads",
    is_owner=True,
)
async def ads_bolum_handler(call: types.CallbackQuery, state: FSMContext):
    res = await db.count_ads()
    if int(res) >= 10:
        await call.answer(
            "Iltmos reklama tugmalarini kamayting eng ko'pi 10tagacha reklama tugmalarini qoshishiz mumkin!",
            show_alert=True,
        )
        return
    await call.message.edit_text(
        "Reklama text kirting!", reply_markup=adminKeyboard.back_panel()
    )
    await state.set_state("ads_add")


@dp.message_handler(content_types=["text"], is_owner=True, state="ads_add")
async def send_users_ads_handler(message: types.Message, state: FSMContext):
    await db.add_ads(ads_text=message.text)
    await message.answer(
        "Reklama text qoshildi!", reply_markup=adminKeyboard.back_panel()
    )
    await state.finish()


@dp.callback_query_handler(
    text="delete_ads",
    state="*",
    is_owner=True,
)
async def delete_ads_handler(call: types.CallbackQuery):
    result = await db.select_all_ads()
    if result:
        keyboard = types.InlineKeyboardMarkup(row_width=5)
        text = "Kerakli reklama ni ochirish uchun tartib raqam boyicha tanlang\n\n"
        for x in result:
            text += f"{x['id']}.{x['ads_text']}\n"
            keyboard.add(
                types.InlineKeyboardButton(text=x["id"], callback_data=f'pd_{x["id"]}')
            )
        keyboard.row(types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="panel"))
        await call.message.edit_text(text, reply_markup=keyboard)
    else:
        await call.answer("Kechirasiz hali reklama qo'shilmagan!", show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith("pd_"), is_owner=True, state="*")
async def delete_channel_handler(call: types.CallbackQuery):
    channel_id = call.data.replace("pd_", "")
    await db.delete_ads(id=int(channel_id))
    await call.message.edit_text(
        "ADS OCHIRILDI!", reply_markup=await adminKeyboard.ads_settings()
    )


# Todo: Send message Function
@dp.callback_query_handler(text="send_users", is_owner=True, state="*")
async def send_users_handler(message: types.CallbackQuery, state: FSMContext):
    nres = await db.select_mailing()
    bot_ = await bot.get_me()
    if nres:
        res = dict(nres)
        user = bot_.username
        (
            id,
            status,
            user_id,
            message_id,
            reply_markup,
            mail_type,
            offset,
            send,
            not_send,
            type,
            location,
            created_at,
        ) = res.values()
        sends = send + not_send
        if not status:
            tz = False
            status = "To'xtatilgan"
        else:
            tz = True
            status = "Davom etmoqda"
        if type == "users":
            type = "👤 Userlarga"
            all_user = await db.count_all_users()
        if type == "groups":
            type = f"👥 Guruhlarga"
            all_user = await db.count_all_groups()

        if int(sends) == all_user["active"]:
            status = f"<b>📧 Xabar yuborish tugadi</b>"
        date1 = created_at
        date2 = datetime.now()
        interval = date2 - date1
        days = interval.days
        hours, remainder = divmod(interval.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        formattedDuration = [
            f"{days} kun" if days else "",
            f"{hours} soat" if hours else "",
            f"{minutes} daqiqa" if minutes else "",
            f"{remainder} sekund" if remainder else "",
        ]
        duration = ", ".join(filter(None, formattedDuration))
        keyboard = await adminKeyboard.mail_sending(s="s", status=tz)
        txsts = ""
        if location == "uz":
            txsts += "📫 Kimlarga yuborilmoqda: O'zbek"
        if location == "uz-Cyrl":
            txsts += "📫 Kimlarga yuborilmoqda: O'zbek-Cyrl"
        elif location == "ru":
            txsts += "📫 Kimlarga yuborilmoqda: Rus"
        elif location == "en":
            txsts += "📫 Kimlarga yuborilmoqda: Ingliz"
        elif location == "groups":
            txsts += "📫 Kimlarga yuborilmoqda: Guruhlarga"
        else:
            txsts += "📫 Kimlarga yuborilmoqda: Hamma"

        text = (
            f"📨 Xabar yuborish\n\n"
            f"Xabar yuborilmoqda: {type}\n"
            f"{txsts}\n"
            f"✅ Yuborilgan: {send}\n"
            f"❌ Yuborilmagan: {not_send}\n"
            f"👥 Umumiy: {sends}/{all_user['active']}\n"
            f"📊 Status: {status}\n\n"
            f"📅 <b>Habar yuborish uchun sarflangan vaqt:</b> <code>{duration}</code>"
        )
        try:
            await message.message.edit_text(text, reply_markup=keyboard)
        except Exception as e:
            logging.error(e)
            await message.answer()
        return
    text = "Qayerga xabar yuborishni istaysiz?"
    await message.message.edit_text(
        text, reply_markup=adminKeyboard.send_bots_keyboard()
    )


@dp.callback_query_handler(
    lambda c: c.data.startswith("pause_or_resume|"), is_owner=True, state="*"
)
async def location_all_handler(message: types.CallbackQuery, state: FSMContext):
    infolist = message.data.split("|")[1]
    if infolist == "s":
        res = await db.select_mailing()
        if res["status"]:
            try:
                os.system("systemctl stop " + MESSAGE_SENDER_COMMAND)
            except Exception as e:
                logging.error(e)
            await db.update_mailing_status(status=False, id=res["id"])
        else:
            try:
                os.system("systemctl restart " + MESSAGE_SENDER_COMMAND)
            except Exception as e:
                logging.error(e)
            await db.update_mailing_status(status=True, id=res["id"])
    nres = await db.select_mailing()
    bot_ = await bot.get_me()
    if nres:
        all_user = await db.count_all_users()
        res = dict(nres)
        user = bot_.username
        (
            id,
            status,
            user_id,
            message_id,
            reply_markup,
            mail_type,
            offset,
            send,
            not_send,
            type,
            location,
            created_at,
        ) = res.values()
        sends = send + not_send
        if not status:
            tz = False
            status = "To'xtatilgan"
        else:
            tz = True
            status = "Davom etmoqda"
        if type == "users":
            type = "👤 Userlarga"
        if int(sends) == all_user["active"]:
            status = f"<b>📧 Xabar yuborish tugadi</b>"
        date1 = created_at
        date2 = datetime.now()
        interval = date2 - date1
        days = interval.days
        hours, remainder = divmod(interval.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        formattedDuration = [
            f"{days} kun" if days else "",
            f"{hours} soat" if hours else "",
            f"{minutes} daqiqa" if minutes else "",
            f"{remainder} sekund" if remainder else "",
        ]
        duration = ", ".join(filter(None, formattedDuration))
        keyboard = await adminKeyboard.mail_sending(s="s", status=tz)
        txsts = ""
        if location == "uz":
            txsts += "📫 Kimlarga yuborilmoqda: O'zbek"
        if location == "uz-Cyrl":
            txsts += "📫 Kimlarga yuborilmoqda: O'zbek-Cyrl"
        elif location == "ru":
            txsts += "📫 Kimlarga yuborilmoqda: Rus"
        elif location == "en":
            txsts += "📫 Kimlarga yuborilmoqda: Ingliz"
        elif location == "groups":
            txsts += "📫 Kimlarga yuborilmoqda: Guruhlarga"
        else:
            txsts += "📫 Kimlarga yuborilmoqda: Hamma"
        text = (
            f"📨 Xabar yuborish\n\n"
            f"Xabar yuborilmoqda: {type}\n"
            f"{txsts}\n"
            f"✅ Yuborilgan: {send}\n"
            f"❌ Yuborilmagan: {not_send}\n"
            f"👥 Umumiy: {sends}/{all_user['active']}\n"
            f"📊 Status: {status}\n\n"
            f"📅 <b>Habar yuborish uchun sarflangan vaqt:</b> <code>{duration}</code>"
        )
        try:
            await message.message.edit_text(text, reply_markup=keyboard)
        except Exception as e:
            logging.error(e)
            await message.answer()


@dp.callback_query_handler(
    lambda c: c.data.startswith("delete_mail|"), is_owner=True, state="*"
)
async def location_all_handler(message: types.CallbackQuery, state: FSMContext):
    await state.finish()
    infolist = message.data.split("|")[1]
    if infolist == "s":
        await db.delete_mailing()
    await message.message.delete()
    await message.message.answer(
        "<b>Xabar yuborish to'xtatildi</b>", reply_markup=adminKeyboard.back_panel()
    )


@dp.callback_query_handler(text="sendUsers", is_owner=True, state="*")
async def send_users_handler(message: types.CallbackQuery, state: FSMContext):
    await message.message.edit_text(
        "Qaysi turdagi auditoriya uchun xabar yuborishni xohlaysiz? "
        "Foydalanuvchilarga yoki guruhlarga? Tanlang: 🔻",
        reply_markup=await adminKeyboard.sender_types(),
    )


@dp.callback_query_handler(text_startswith="location_", is_owner=True, state="*")
async def send_users_handler(message: types.CallbackQuery, state: FSMContext):
    await state.update_data(local=message.data.replace("location_", ""))
    if message.data.replace("location_", "") == "groups":
        text = (
            "Guruhlarga yuboriladigan xabarni kiriting,"
            " kontent turi ixtiyoriy.\n\n"
            "Foydalanish imkonsiz: location, contact, poll, game, invoice, successful_payment"
        )
    else:
        text = (
            "Foydalanuvchilarga yuboriladigan xabarni kiriting,"
            " kontent turi ixtiyoriy.\n\n"
            "Foydalanish imkonsiz: location, contact, poll, game, invoice, successful_payment"
        )
    await message.message.edit_text(
        text,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="panel")
        ),
    )
    await state.set_state("SendFormAllUsersBot")


@dp.message_handler(
    content_types=[
        "photo",
        "voice",
        "text",
        "sticker",
        "animation",
        "video",
        "video_note",
        "audio",
    ],
    is_owner=True,
    state="SendFormAllUsersBot",
)
async def send_users_ads_handler(message: types.Message, state: FSMContext):
    info = await state.get_data()
    message_id = message.message_id
    reply_markup = ""
    chat_id = message.chat.id
    if message.reply_markup:
        reply_markup = json.dumps(message.reply_markup.as_json(), ensure_ascii=False)

    res = await db.add_new_mailing(
        user_id=chat_id,
        message_id=message_id,
        reply_markup=str(reply_markup),
        mail_type="oddiy",
        type="groups" if info["local"] == "groups" else "users",
        location=info["local"],
    )
    if res:
        await message.answer("Xabar yuborish boshlandi")
        await state.finish()
    else:
        await message.answer("Xatolik yuz berdi")
        await state.finish()


@dp.callback_query_handler(
    state="*",
    text="admin_add",
    is_owner=True,
)
async def ads_bolum_handler(call: types.CallbackQuery, state: FSMContext):
    text = (
        "Yaxshi. Admin qilmoqchi bo'lgan odamingizning ID raqamini menga yuboring: 🔻"
    )
    await call.message.edit_text(text, reply_markup=adminKeyboard.back_panel())
    await state.set_state("AddAdminState")


@dp.message_handler(
    is_owner=True,
    state="AddAdminState",
    content_types=["text"],
)
async def admin_add_handler(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        await state.finish()
        get_admin = await db.select_admin(user_id=str(message.text))
        if get_admin:
            try:
                await message.answer(
                    text="❗️ Bu ID raqam bilan avval admin qo'shilgan.",
                    reply_markup=adminKeyboard.back_panel(),
                )
            except:
                pass
        else:
            try:
                await message.answer(
                    text="Admin muvaffaqiyatli qo'shildi.",
                    reply_markup=adminKeyboard.back_panel(),
                )
            except:
                pass
        if not get_admin:

            try:
                await db.add_admins(user_id=str(message.text))
            except:
                pass

    else:
        try:
            await message.answer(text="❗️ ID raqamni faqat raqamlar orqali kiriting.")
        except:
            pass


@dp.callback_query_handler(state="*", text="admin_remove", is_owner=True)
async def admin_remove_handler(call: types.CallbackQuery):
    admins = await db.select_all_admins()
    if admins:
        button = InlineKeyboardMarkup()
        for admin in admins:
            admin_name = await bot.get_chat(chat_id=admin["user_id"])
            button.add(
                InlineKeyboardButton(
                    text=admin_name.full_name,
                    callback_data="del-admin-" + str(admin["id"]),
                )
            )

        button.add(InlineKeyboardButton(text="🚫 Bekor qilish", callback_data="panel"))
        try:
            await call.answer()
            await call.message.edit_text(
                text="Qaysi adminni o'chirishni xohlaysiz? Tanlang: 🔻",
                reply_markup=button,
            )
        except:
            pass
    else:
        try:
            await call.answer(
                text="❗️ Hozirda bot adminlari mavjud emas.", show_alert=False
            )
        except:
            pass


@dp.callback_query_handler(
    text_startswith="del-admin-",
    state="*",
    is_owner=True,
)
async def del_admin_worker(call: types.CallbackQuery):
    admin_id = int(call.data.replace("del-admin-", ""))
    select_admin = await db.select_admin(id=admin_id)
    if select_admin["user_id"] != str(call.from_user.id):

        await db.delete_admin(id=admin_id)
        try:
            await call.answer()
            await call.message.edit_text(
                text="Admin muvaffaqiyatli o'chirib tashlandi. "
                "Xo'sh nima qilamiz? Tanlang: 🔻",
                reply_markup=adminKeyboard.back_panel(),
            )
        except:
            pass
    else:
        try:
            await call.answer(
                text="❗️ Siz o'zingizni adminlikdan o'chirib yubora olmaysiz.",
                show_alert=True,
            )
        except:
            pass


@dp.callback_query_handler(
    state="*",
    text="ads_media",
    is_owner=True,
)
async def ads_bolum_handler(call: types.CallbackQuery, state: FSMContext):
    text = (
        "Yaxshi reklama post habarini kiriting,"
        " kontent turi ixtiyoriy.\n\n"
        "Foydalanish imkonsiz: location, contact, poll, game, invoice, successful_payment"
    )
    await call.message.edit_text(text, reply_markup=adminKeyboard.back_panel())
    await state.set_state("AddMediaState")


@dp.message_handler(
    content_types=[
        "photo",
        "voice",
        "text",
        "sticker",
        "animation",
        "video",
        "video_note",
        "audio",
    ],
    is_owner=True,
    state="AddMediaState",
)
async def send_users_ads_handler(message: types.Message, state: FSMContext):
    bot_ = await bot.get_me()
    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    elif message.content_type == "voice":
        file_id = message.voice.file_id
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    elif message.content_type == "text":
        file_id = None
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    elif message.content_type == "sticker":
        file_id = message.sticker.file_id
        caption = None
        type = message.content_type
    elif message.content_type == "animation":
        file_id = message.animation.file_id
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    elif message.content_type == "video":
        file_id = message.video.file_id
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    elif message.content_type == "video_note":
        file_id = message.video_note.file_id
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    elif message.content_type == "audio":
        file_id = message.audio.file_id
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    uuid_url = generate_custom_uuid()
    deepLink = f"https://t.me/{bot_.username}?start={uuid_url}"
    await db.add_posts(
        file_id=str(file_id),
        caption=str(caption),
        content=str(type),
        code=str(uuid_url),
    )
    await message.answer(
        f"🤖 <b>Yangi {type} joylandi, reklama havolasi.\n\n{deepLink}</b>",
        reply_markup=adminKeyboard.back_panel(),
    )
    await state.finish()


@dp.callback_query_handler(
    state="*",
    text="ads_links",
    is_owner=True,
)
async def ads_bolum_handler(call: types.CallbackQuery, state: FSMContext):
    check_links = await db.select_all_referals(limit=99)
    if check_links:
        matn = (
            "🖇 Botdagi barcha reklama havolalari quyidagilar:\n\n"
            "<i>Qaysidir reklama havolasini ko'rish uchun, pastdagi tugmalardan foydalaning.</i>"
        )

        button = InlineKeyboardMarkup()

        for link in check_links:
            button.add(
                InlineKeyboardButton(
                    text=link["code"], callback_data="see-link-{}".format(link["id"])
                )
            )

        button.add(InlineKeyboardButton(text="Bekor qilish 🚫", callback_data="panel"))

        try:
            await call.message.edit_text(text=matn, reply_markup=button)
        except:
            pass
    else:
        await call.answer("❗️ Reklama havolalari topilmadi.", show_alert=True)


@dp.callback_query_handler(text_startswith="see-link", state="*")
async def see_link_callback(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.answer()
    bot_ = await bot.get_me()
    link_num = call.data.replace("see-link-", "")
    check_link = await db.select_referal(id=int(link_num))
    if check_link:
        deepLink = f"https://t.me/{bot_.username}?start={check_link['code']}"
        matn = (
            f"ℹ️ <b>Marhamat, reklama havolasi haqida ma'lumot:</b>\n\n"
            f"🖇 <i>Havola nomi: <code>{check_link['code']}</code>\n"
            f"👤 Foydalanuvchilar: {check_link['members']} (+{check_link['days']})\n"
            f"📆 Oxirgi 1 haftada: {check_link['weekly']} ta obunachi qo'shildi\n\n"
            f"🔗<b> Foydalanuvchilar uchun havola:</b></i> <b>{deepLink}</b>\n"
        )
        button = InlineKeyboardMarkup()
        button.add(
            InlineKeyboardButton(
                text="Yangilash 🔁",
                callback_data="see-link-{}".format(check_link["id"]),
            )
        )
        button.add(
            InlineKeyboardButton(
                text="Havolani o'chirish 🗑",
                callback_data="delete-link-{id}".format(id=link_num),
            )
        )
        button.add(InlineKeyboardButton(text="Orqaga ◀️", callback_data="ads_links"))
        try:
            await call.answer()
            await call.message.edit_text(
                text=matn, reply_markup=button, disable_web_page_preview=True
            )
        except:
            pass
    else:
        await call.answer(
            "❗️ Kechirasiz, qandaydir xatolik yuz berdi.", show_alert=True
        )


@dp.callback_query_handler(
    state="*",
    text_startswith="delete-link-",
    is_owner=True,
)
async def ads_bolum_handler(call: types.CallbackQuery, state: FSMContext):
    link_num = call.data.replace("delete-link-", "")
    await db.delete_referal(id=int(link_num))
    check_links = await db.select_all_referals(limit=99)
    if check_links:
        matn = (
            "🖇 Botdagi barcha reklama havolalari quyidagilar:\n\n"
            "<i>Qaysidir reklama havolasini ko'rish uchun, pastdagi tugmalardan foydalaning.</i>"
        )

        button = InlineKeyboardMarkup()

        for link in check_links:
            button.add(
                InlineKeyboardButton(
                    text=link["code"], callback_data="see-link-{}".format(link["id"])
                )
            )

        button.add(InlineKeyboardButton(text="Bekor qilish 🚫", callback_data="panel"))

        try:
            await call.message.edit_text(text=matn, reply_markup=button)
        except:
            pass
    else:
        await call.message.edit_text(
            "❗️ Reklama havolalari topilmadi.", reply_markup=adminKeyboard.back_panel()
        )


@dp.callback_query_handler(
    text="update_tops",
    state="*",
)
async def export_data(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.answer()
        sended_message = await call.message.edit_text(
            text="❗️ Iltimos, biroz kuting. Jarayon ko'proq vaqt olishi mumkin."
        )
    except:
        sended_message = None
    top_tracks = await get_top_musics(limit=100, offset=0)
    await db.add_tops(top_tracks)
    if sended_message != None:
        try:
            await sended_message.delete()
        except:
            pass
    await call.message.answer(
        "❗️ <b>TOP CHART YANGILANDI</b>", reply_markup=adminKeyboard.back_panel()
    )


@dp.callback_query_handler(
    state="*",
    text="add_startads",
    is_owner=True,
)
async def ads_bolum_handler(call: types.CallbackQuery, state: FSMContext):
    result = await db.select_sps()
    if result:
        await call.answer(
            "❗️ Kechirasiz Avval Post qo'shgansiz buni ochirib keyin qayta urinb ko'ring.",
            show_alert=True,
        )
        return
    text = (
        "Yaxshi reklama post habarini kiriting,"
        " kontent turi ixtiyoriy.\n\n"
        "Foydalanish imkonsiz: location, contact, poll, game, invoice, successful_payment"
    )
    await call.message.edit_text(text, reply_markup=adminKeyboard.back_panel())
    await state.set_state("AddMediaSPSState")


@dp.message_handler(
    content_types=[
        "photo",
        "voice",
        "text",
        "sticker",
        "animation",
        "video",
        "video_note",
        "audio",
    ],
    is_owner=True,
    state="AddMediaSPSState",
)
async def send_users_ads_handler(message: types.Message, state: FSMContext):
    bot_ = await bot.get_me()
    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    elif message.content_type == "voice":
        file_id = message.voice.file_id
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    elif message.content_type == "text":
        file_id = None
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    elif message.content_type == "sticker":
        file_id = message.sticker.file_id
        caption = None
        type = message.content_type
    elif message.content_type == "animation":
        file_id = message.animation.file_id
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    elif message.content_type == "video":
        file_id = message.video.file_id
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    elif message.content_type == "video_note":
        file_id = message.video_note.file_id
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    elif message.content_type == "audio":
        file_id = message.audio.file_id
        try:
            caption = message.html_text
        except:
            caption = None
        type = message.content_type
    uuid_url = generate_custom_uuid()
    reply_markup = ""
    if message.reply_markup:
        reply_markup = json.dumps(message.reply_markup.as_json(), ensure_ascii=False)
    await db.add_sps(
        file_id=str(file_id),
        caption=str(caption),
        content=str(type),
        reply_markup=str(reply_markup),
    )
    await message.answer(
        f"🤖 <b>Yangi {type} reklama posti joylandi</b>",
        reply_markup=adminKeyboard.back_panel(),
    )
    await state.finish()


@dp.callback_query_handler(
    state="*",
    text="remove_startads",
    is_owner=True,
)
async def ads_bolum_handler(call: types.CallbackQuery, state: FSMContext):
    result = await db.select_sps()
    if result:
        await call.message.edit_text(
            "❗️ Rostdan ham postni o'chirmoqchimisiz?",
            reply_markup=InlineKeyboardMarkup().row(
                InlineKeyboardButton(text="✅", callback_data="yespos"),
                InlineKeyboardButton(text="❌", callback_data="panel"),
            ),
        )
    else:
        await call.answer("❗️ Kechirasiz reklama posti topilmadi", show_alert=True)


@dp.callback_query_handler(
    state="*",
    text="yespos",
    is_owner=True,
)
async def ads_bolum_handler(call: types.CallbackQuery, state: FSMContext):
    await db.truncate_sps()
    await call.message.edit_text(
        "❗️ Post o'chirildi.", reply_markup=adminKeyboard.menu()
    )


@dp.callback_query_handler(
    text="export_data",
    state="*",
)
async def export_data(call: types.CallbackQuery, state: FSMContext):
    await state.finish()

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text="👤 Foydalanuvchilar (.sql)", callback_data="get-id-users"
        )
    )
    keyboard.add(
        InlineKeyboardButton(text="👥 Guruhlar (.sql)", callback_data="get-id-groups")
    )
    keyboard.add(
        InlineKeyboardButton(
            text="🗞 Barcha ma'lumotlar (.sql)", callback_data="get-id-all"
        )
    )
    keyboard.add(InlineKeyboardButton(text="🚫 Bekor qilish", callback_data="panel"))

    await call.message.edit_text(
        text="📦 Ma'lumotlarni qaysi usulda olmoqchisiz? "
        "Xohlagan bittasni tanlashingiz mumkin: 🔻",
        reply_markup=keyboard,
    )


@dp.callback_query_handler(
    text="get-id-users",
    state="*",
)
async def export_data(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        await call.answer()
        sended_message = await call.message.edit_text(
            text="❗️ Iltimos, biroz kuting. Jarayon ko'proq vaqt olishi mumkin."
        )
    except:
        sended_message = None

    if sended_message != None:
        try:
            await sended_message.delete()
        except:
            pass
    try:
        result = await asyncio.create_subprocess_shell(
            'pg_dump "host='
            + DATABASE_INFO["host"]
            + " port=5432 dbname="
            + DATABASE_INFO["database"]
            + " user="
            + DATABASE_INFO["user"]
            + " password="
            + DATABASE_INFO["password"]
            + '" -E utf-8 -t users > '
            + DATABASE_INFO["database"]
            + "_users.sql"
        )
        await result.communicate()
    except:
        pass

    medias = []
    medias += [
        InputMediaDocument(
            media=InputFile(path_or_bytesio=DATABASE_INFO["database"] + "_users.sql")
        )
    ]

    try:
        await call.message.answer_media_group(media=medias)
    except:
        pass

    try:
        os.remove(DATABASE_INFO["database"] + "_users.sql")
    except:
        pass

    if sended_message != None:
        try:
            await sended_message.delete()
        except:
            pass


@dp.callback_query_handler(
    text="get-id-groups",
    state="*",
)
async def export_data(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        await call.answer()
        sended_message = await call.message.edit_text(
            text="❗️ Iltimos, biroz kuting. Jarayon ko'proq vaqt olishi mumkin."
        )
    except:
        sended_message = None

    if sended_message != None:
        try:
            await sended_message.delete()
        except:
            pass
    try:
        result = await asyncio.create_subprocess_shell(
            'pg_dump "host='
            + DATABASE_INFO["host"]
            + " port=5432 dbname="
            + DATABASE_INFO["database"]
            + " user="
            + DATABASE_INFO["user"]
            + " password="
            + DATABASE_INFO["password"]
            + '" -E utf-8 -t groups > '
            + DATABASE_INFO["database"]
            + "_groups.sql"
        )
        await result.communicate()
    except:
        pass

    medias = []
    medias += [
        InputMediaDocument(
            media=InputFile(path_or_bytesio=DATABASE_INFO["database"] + "_groups.sql")
        )
    ]

    try:
        await call.message.answer_media_group(media=medias)
    except:
        pass

    try:
        os.remove(DATABASE_INFO["database"] + "_groups.sql")
    except:
        pass

    if sended_message != None:
        try:
            await sended_message.delete()
        except:
            pass


@dp.callback_query_handler(
    text="get-id-all",
    state="*",
)
async def export_data(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        await call.answer()
        sended_message = await call.message.edit_text(
            text="❗️ Iltimos, biroz kuting. Jarayon ko'proq vaqt olishi mumkin."
        )
    except:
        sended_message = None

    if sended_message != None:
        try:
            await sended_message.delete()
        except:
            pass

    try:
        result = await asyncio.create_subprocess_shell(
            'pg_dump "host='
            + DATABASE_INFO["host"]
            + " port=5432 dbname="
            + DATABASE_INFO["database"]
            + " user="
            + DATABASE_INFO["user"]
            + " password="
            + DATABASE_INFO["password"]
            + '" -E utf-8 > '
            + DATABASE_INFO["database"]
            + ".sql"
        )
        await result.communicate()
    except:
        pass

    medias = []
    medias += [
        InputMediaDocument(
            media=InputFile(path_or_bytesio=DATABASE_INFO["database"] + ".sql")
        )
    ]

    try:
        await call.message.answer_media_group(media=medias)
    except:
        pass

    try:
        os.remove(DATABASE_INFO["database"] + ".sql")
    except:
        pass

    if sended_message != None:
        try:
            await sended_message.delete()
        except:
            pass
