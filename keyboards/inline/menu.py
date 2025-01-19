from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.config import lang_file
from loader import db, bot
from utils.language import LangSet


async def language_keyboard(user_id):
    lang = await db.get_user_lang(user_id=user_id)
    k = []
    markup = InlineKeyboardMarkup(row_width=2)
    for key in lang_file:
        text = f"{lang_file[key]['emoji']} {lang_file[key]['nativeName']} "
        if lang["lang"] == key:
            text += "✅"
        k.append(InlineKeyboardButton(text=text, callback_data="language_" + key))
    markup.add(*k)
    return markup


async def add_keyboard(user_id):
    text = await LangSet(user_id).get_translation("add_button")
    markup = InlineKeyboardMarkup()
    bot_ = await bot.get_me()
    markup.add(
        InlineKeyboardButton(
            text=text, url=f"https://t.me/{bot_.username}?startgroup=true"
        )
    )
    return markup


async def search_keyboard(user_id):
    text = await LangSet(user_id).get_translation("add_button")
    dtext = await LangSet(user_id).get_translation("download_music")
    markup = InlineKeyboardMarkup()
    bot_ = await bot.get_me()
    markup.add(InlineKeyboardButton(text=dtext, callback_data="download_music"))
    markup.add(
        InlineKeyboardButton(
            text=text, url=f"https://t.me/{bot_.username}?startgroup=true"
        )
    )
    return markup


"""
    textuz += "..." if code == 'UZ' else f"🇺🇿"
    textgb += "..." if code == 'GB' else f" 🇬🇧"
    textru += "..." if code == 'RU' else "🇷🇺"
    textkg += "..." if code == 'KG' else "🇰🇬"
    textkz += "..." if code == 'KZ' else "🇰🇿"
    texttr += "..." if code == 'TR' else "🇹🇷"
    text += "..." if code == 'AZ' else "🇦🇿"
"""

options = {
    "UZ": {"emoji": f"🇺🇿"},
    "GB": {"emoji": f"🇬🇧"},
    "RU": {"emoji": f"🇷🇺"},
    "KZ": {"emoji": f"🇰🇿"},
    "TR": {"emoji": f"🇹🇷"},
    "AZ": {"emoji": f"🇦🇿"},
}


async def top_chart_country(code):
    markup = []
    for key, value in options.items():
        if key == code:
            button_text = f"{value['emoji']} ✅"
        else:
            button_text = value["emoji"]
        markup.append(
            InlineKeyboardButton(text=button_text, callback_data=f"get-country-{key}")
        )
    return markup
