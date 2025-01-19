import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import exceptions

from data.config import lang_file
from loader import db, bot


class AdminKeyboards:

    def menu(self):
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton(text="📊 Statistika", callback_data="stat"),
            InlineKeyboardButton(text="📝 Xabar yuborish", callback_data="send_users"),
        )
        keyboard.row(
            InlineKeyboardButton(
                text="⚙️ Majburiy a'zolik sozlamalari", callback_data="force_settings"
            )
        )
        keyboard.row(
            InlineKeyboardButton(text="⚙️ Reklama bo'limi", callback_data="ads_bolum"),
            InlineKeyboardButton(text="⚙️ Media qo'shish", callback_data="ads_media"),
        )
        keyboard.row(
            InlineKeyboardButton(text="🖇 Reklama havolalari", callback_data="ads_links")
        )
        keyboard.add(
            InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin_add"),
            InlineKeyboardButton(
                text="➖ Admin o'chirish", callback_data="admin_remove"
            ),
        )

        keyboard.add(
            InlineKeyboardButton(text="➕ Post qo'shish", callback_data="add_startads"),
            InlineKeyboardButton(
                text="➖ Post o'chirish", callback_data="remove_startads"
            ),
        )
        keyboard.row(
            InlineKeyboardButton(
                text="📦 Ma'lumotlar ombori", callback_data="export_data"
            )
        )
        keyboard.row(
            InlineKeyboardButton(
                text="🔄 Update top chart", callback_data="update_tops"
            )
        )
        keyboard.row(InlineKeyboardButton(text="🔼", callback_data="close"))
        return keyboard

    def back_panel(self):
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text="⬅️ Ortga", callback_data="panel"))
        return keyboard

    async def force_settings(self):
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton(text="📢 Kanallar", callback_data="channels"),
            InlineKeyboardButton(text="🤖 Botlar", callback_data="bots"),
        )
        status = await db.select_settings()
        if status["value"] == "True":
            text = "✅ Majburiy a'zolik | Yoqilgan"
        else:
            text = "❌ Majburiy a'zolik | O'chirilgan"
        keyboard.row(InlineKeyboardButton(text=text, callback_data="channels_on_off"))
        keyboard.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="panel"))

        return keyboard

    async def channel_settings(self):
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton(text="📢 Kanallar", callback_data="channels_list")
        )
        keyboard.row(
            InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_channel"),
            InlineKeyboardButton(
                text="➖ Kanal o'chirish", callback_data="delete_channel"
            ),
        )
        keyboard.row(
            InlineKeyboardButton(text="⬅️ Ortga", callback_data="force_settings")
        )

        return keyboard

    async def bots_keyboard(self):
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton(text="📢 Botlar", callback_data="bots_list"))
        keyboard.row(
            InlineKeyboardButton(text="➕ Bot qo'shish", callback_data="bot_add"),
            InlineKeyboardButton(text="➖ Bot o'chirish", callback_data="delbot"),
        )
        keyboard.row(
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="force_settings")
        )
        return keyboard

    async def ads_settings(self):
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton(text="➕ ADS qo'shish", callback_data="add_ads"),
            InlineKeyboardButton(text="➖ ADS o'chirish", callback_data="delete_ads"),
        )
        keyboard.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="panel"))

        return keyboard

    async def channels_list(self):
        keyboard = InlineKeyboardMarkup()
        result = await db.select_all_channels()
        if result:
            for channel in result:
                try:
                    channel = await bot.get_chat(channel["channel_id"])
                    count = await bot.get_chat_member_count(channel.id)
                    if count > 1000:
                        count = f"{round(count / 1000, 1)}K"
                except Exception as e:
                    logging.error(e)
                    continue
                keyboard.row(
                    InlineKeyboardButton(
                        text=f"{channel.title} [{count}]",
                        callback_data=f"channel_{channel.id}",
                    )
                )
            keyboard.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="channels"))

            return keyboard
        else:
            return False

    async def delete_bots(self):
        try:
            keyboard = InlineKeyboardMarkup(row_width=1)
            result = await db.select_all_bots()
            if result:
                for x in result:
                    try:
                        bot = Bot(token=x["bot_token"])
                        title = await bot.get_me()
                    except exceptions.ValidationError:
                        logging.error("Token validation")
                        continue
                    except exceptions.Unauthorized:
                        logging.error("Telegram unauthorized")
                        continue
                    keyboard.add(
                        InlineKeyboardButton(
                            text=f"{title.full_name}", callback_data=f'dd_{x["id"]}'
                        )
                    )

                keyboard.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="bots"))

                return keyboard
            else:
                return False
        except:
            return False

    async def bots_list(self):
        try:
            keyboard = InlineKeyboardMarkup(row_width=1)
            result = await db.select_all_bots()
            if result:
                for x in result:
                    try:
                        bot = Bot(token=x["bot_token"])
                        title = await bot.get_me()
                    except exceptions.ValidationError:
                        logging.error("Token validation")
                        continue
                    except exceptions.Unauthorized:
                        logging.error("Telegram unauthorized")
                        continue
                    keyboard.add(
                        InlineKeyboardButton(
                            text=f"{title.full_name}", url=f"{x['bot_link']}"
                        )
                    )

                keyboard.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="bots"))

                return keyboard
            else:
                return False
        except:
            return False

    async def delete_channels(self):
        keyboard = InlineKeyboardMarkup()
        result = await db.select_all_channels()
        if result:
            for channel in result:
                try:
                    channel = await bot.get_chat(channel["channel_id"])
                    count = await bot.get_chat_member_count(channel.id)
                    if count > 1000:
                        count = f"{round(count / 1000, 1)}K"
                except Exception as e:
                    logging.error(e)
                    continue
                keyboard.row(
                    InlineKeyboardButton(
                        text=f"{channel.title} [{count}]",
                        callback_data=f"delete_channel_{channel.id}",
                    )
                )
            keyboard.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="channels"))

            return keyboard
        else:
            return False

    def send_bots_keyboard(self):
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton(text=f"👤 Userlarga", callback_data="sendUsers"),
            InlineKeyboardButton(
                text=f"👥 Guruhlarga", callback_data="location_groups"
            ),
        )
        keyboard.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="panel"))
        return keyboard

    async def sender_types(self):
        keyboard = InlineKeyboardMarkup(row_width=2)

        for key in lang_file:
            text = f"{lang_file[key]['emoji']} {lang_file[key]['nativeName']} "

            keyboard.insert(
                InlineKeyboardButton(text=text, callback_data="location_" + key)
            )
        keyboard.row(
            InlineKeyboardButton(text="🌏 Barchaga", callback_data="location_all")
        )
        keyboard.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="send_users"))
        return keyboard

    async def mail_sending(self, s: str, status=None):
        keyboard = InlineKeyboardMarkup(row_width=1)
        if status:
            pause_or_resume = "To'xtatish ⏸"
        else:
            pause_or_resume = "Davom etish ▶️"

        if status != None:
            keyboard.add(
                InlineKeyboardButton(
                    text=pause_or_resume, callback_data=f"pause_or_resume|{s}"
                )
            )
        keyboard.add(
            InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"send_users")
        )
        keyboard.add(
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_mail|{s}")
        )
        keyboard.add(InlineKeyboardButton(text="⬅️ Ortga", callback_data="panel"))

        return keyboard


adminKeyboard = AdminKeyboards()
