import logging

from aiofiles import os
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import (
    ChatType,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)

from data.config import MEDIA_DIRECTORY
from keyboards.inline.menu import top_chart_country, add_keyboard
from libs.download_music import SearchMusic
from libs.recognizer_helpers import download_file, recognize_voice
from loader import dp, db
from utils.language import LangSet


@dp.message_handler(
    content_types=["voice", "video_note", "video", "audio"],
    state="*",
)
async def recognize_music_handler(msg: types.Message, state: FSMContext):
    if msg.chat.type in ["group", "supergroup"]:
        check_user = await db.select_group(user_id=int(msg.chat.id))
        if not check_user:
            try:
                await db.add_group(user_id=int(msg.chat.id))
            except Exception as err:
                logging.error(err)

    user_id = msg.from_user.id
    if msg.chat.type == "private":
        try:
            sended_message = await msg.answer("🔎", reply=True)
        except:
            sended_message = None
    else:
        sended_message = None
    if msg.voice:
        file_size = (msg.voice.file_size / 1024) / 1024
    elif msg.video_note:
        file_size = (msg.video_note.file_size / 1024) / 1024
    elif msg.audio:
        file_size = (msg.audio.file_size / 1024) / 1024
    else:
        file_size = (msg.video.file_size / 1024) / 1024

    if file_size > 20:
        if msg.chat.type == "private":
            try:
                bots_answer = await msg.answer(
                    text=await LangSet(user_id).get_translation(
                        "SENDED_FILE_IS_TOO_LARGE"
                    ),
                    reply=True,
                )
            except:
                pass
    else:
        if msg.voice:
            is_downloaded = await download_file(
                file_id=msg.voice.file_id,
                chat_id=str(msg.chat.id) + "-" + str(msg.message_id),
            )
        elif msg.video_note:
            is_downloaded = await download_file(
                file_id=msg.video_note.file_id,
                chat_id=str(msg.chat.id) + "-" + str(msg.message_id),
            )
        elif msg.audio:
            is_downloaded = await download_file(
                file_id=msg.audio.file_id,
                chat_id=str(msg.chat.id) + "-" + str(msg.message_id),
            )
        else:
            is_downloaded = await download_file(
                file_id=msg.video.file_id,
                chat_id=str(msg.chat.id) + "-" + str(msg.message_id),
            )

        if is_downloaded:
            track_info = await recognize_voice(
                MEDIA_DIRECTORY + str(msg.chat.id) + "-" + str(msg.message_id) + ".ogg"
            )
            try:
                if track_info["status"]:
                    try:
                        bots_answer = await msg.answer_photo(
                            photo=track_info["thumbnail"],
                            caption=f"🎵 <b>{track_info['subtitle']} - {track_info['title']}</b>",
                            reply=True,
                        )
                    except:
                        bots_answer = None

                    if sended_message is not None:
                        await sended_message.delete()

                    sended_message = None

                    searched_musics = await SearchMusic.search_music(
                        query=f"{track_info['subtitle']} - {track_info['title']}",
                        limit=5,
                        ignore_results=True,
                    )
                    if searched_musics:
                        if msg.chat.type == "private":
                            keyboard = InlineKeyboardMarkup(row_width=5)
                        else:
                            keyboard = InlineKeyboardMarkup(row_width=10)
                        caption = "<b>" + bots_answer.caption + "</b>\n\n"

                        if track_info["lyrics"] is not None:
                            keyboard.add(
                                InlineKeyboardButton(
                                    text=await LangSet(user_id).get_translation(
                                        "LYRICS_MESSAGE"
                                    ),
                                    callback_data=f'get-lyrics-{track_info["track_id"]}',
                                )
                            )

                        for i, music in enumerate(searched_musics):
                            if msg.chat.type == "private":
                                k = InlineKeyboardButton(
                                    text=str(i + 1),
                                    callback_data=f'download-music-{music["music_id"]}',
                                )
                                caption += f"{i + 1}. <i>{music['title']}</i>\n"

                                # k = InlineKeyboardButton(text=music['title'],
                                #                          callback_data=f'download-music-{music["music_id"]}')
                            else:
                                k = InlineKeyboardButton(
                                    text=str(i + 1),
                                    callback_data=f'download-music-{music["music_id"]}',
                                )
                                caption += f"{i + 1}. <i>{music['title']}</i>\n"

                            if i == 0:
                                keyboard.add(k)
                            else:
                                keyboard.insert(k)

                        if bots_answer is not None:
                            await bots_answer.edit_caption(
                                caption=caption, reply_markup=keyboard
                            )

                else:
                    if msg.chat.type == "private":
                        bots_answer = await msg.answer(
                            await LangSet(user_id).get_translation(
                                "MUSIC_NOT_FINDED_MESSAGE"
                            ),
                            reply=True,
                            reply_markup=await add_keyboard(user_id),
                        )

            except:
                if msg.chat.type == "private":
                    if bots_answer is not None:
                        await bots_answer.delete()

                    try:
                        bots_answer = await msg.answer(
                            await LangSet(user_id).get_translation("ERROR_MESSAGE"),
                            reply=True,
                        )
                    except:
                        pass
        else:
            if msg.chat.type == "private":
                try:
                    bots_answer = await msg.answer(
                        await LangSet(user_id).get_translation("ERROR_MESSAGE"),
                        reply=True,
                    )
                except:
                    pass

        if is_downloaded:
            await os.remove(
                MEDIA_DIRECTORY + str(msg.chat.id) + "-" + str(msg.message_id) + ".ogg"
            )

        if sended_message is not None:
            await sended_message.delete()


@dp.callback_query_handler(text="download_music", state="*")
async def download_music_handler(call: CallbackQuery):
    file_id = call.message.video.file_id
    user_id = call.from_user.id
    await call.answer(await LangSet(user_id).get_translation("searching"))
    is_downloaded = await download_file(
        file_id=file_id,
        chat_id=str(call.message.chat.id) + "-" + str(call.message.message_id),
    )

    if is_downloaded:
        track_info = await recognize_voice(
            MEDIA_DIRECTORY
            + str(call.message.chat.id)
            + "-"
            + str(call.message.message_id)
            + ".ogg"
        )
        try:
            if track_info["status"]:
                try:
                    bots_answer = await call.message.answer_photo(
                        photo=track_info["thumbnail"],
                        caption=f"🎵 <b>{track_info['subtitle']} - {track_info['title']}</b>",
                        reply=True,
                    )
                except:
                    bots_answer = None

                searched_musics = await SearchMusic.search_music(
                    query=f"{track_info['subtitle']} - {track_info['title']}",
                    limit=5,
                    ignore_results=True,
                )
                if searched_musics:
                    if call.message.chat.type == "private":
                        keyboard = InlineKeyboardMarkup(row_width=5)
                    else:
                        keyboard = InlineKeyboardMarkup(row_width=5)
                    caption = "<b>" + bots_answer.caption + "</b>\n\n"

                    if track_info["lyrics"] is not None:
                        keyboard.add(
                            InlineKeyboardButton(
                                text=await LangSet(user_id).get_translation(
                                    "LYRICS_MESSAGE"
                                ),
                                callback_data=f'get-lyrics-{track_info["track_id"]}',
                            )
                        )

                    for i, music in enumerate(searched_musics):
                        if call.message.chat.type == "private":
                            k = InlineKeyboardButton(
                                text=str(i + 1),
                                callback_data=f'download-music-{music["music_id"]}',
                            )
                            caption += f"{i + 1}. <i>{music['title']}</i>\n"
                        else:
                            k = InlineKeyboardButton(
                                text=str(i + 1),
                                callback_data=f'download-music-{music["music_id"]}',
                            )
                            caption += f"{i + 1}. <i>{music['title']}</i>\n"

                        if i == 0:
                            keyboard.add(k)
                        else:
                            keyboard.insert(k)

                    if bots_answer is not None:
                        await bots_answer.edit_caption(
                            caption=caption, reply_markup=keyboard
                        )

            else:
                if call.message.chat.type == "private":
                    bots_answer = await call.message.answer(
                        await LangSet(user_id).get_translation(
                            "MUSIC_NOT_FINDED_MESSAGE"
                        ),
                        reply=True,
                        reply_markup=await add_keyboard(user_id),
                    )

        except:
            if call.message.chat.type == "private":
                if bots_answer is not None:
                    await bots_answer.delete()

                try:
                    bots_answer = await call.message.answer(
                        await LangSet(user_id).get_translation("ERROR_MESSAGE"),
                        reply=True,
                    )
                except:
                    pass
    else:
        if call.message.chat.type == "private":
            try:
                bots_answer = await call.message.answer(
                    await LangSet(user_id).get_translation("ERROR_MESSAGE"), reply=True
                )
            except:
                pass
    if is_downloaded:
        await os.remove(
            MEDIA_DIRECTORY
            + str(call.message.chat.id)
            + "-"
            + str(call.message.message_id)
            + ".ogg"
        )


@dp.message_handler(commands="top", state="*")
async def top_command(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    language = await db.select_user(user_id=msg.from_user.id)
    if language["lang"] in ["uz", "uz-Cyrl"]:
        language = "UZ"
    elif language["lang"] == "en":
        language = "GB"
    else:
        language = language["lang"].upper()
    countrys = await top_chart_country(code=language)
    top_tracks = await db.select_all_tops(country=language, limit=10)
    if top_tracks:
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.row(*countrys)
        for i, music in enumerate(top_tracks):
            keyboard.add(
                InlineKeyboardButton(
                    text=music["title"],
                    callback_data=f'get-top-music|{music["music_id"]}|0|{language}',
                )
            )

        keyboard.row(
            InlineKeyboardButton(text="⬅️", callback_data=f"go-to-top|0|{language}"),
            InlineKeyboardButton(text="❌", callback_data="delete-message"),
            InlineKeyboardButton(text="➡️", callback_data=f"go-to-top|2|{language}"),
        )
        await msg.answer(
            text=await LangSet(user_id).get_translation("top"), reply_markup=keyboard
        )
    else:
        countrys = await top_chart_country(code="EN")
        top_tracks = await db.select_all_tops(country="EN", limit=10)
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.row(*countrys)
        for i, music in enumerate(top_tracks):
            keyboard.add(
                InlineKeyboardButton(
                    text=music["title"],
                    callback_data=f'get-top-music|{music["music_id"]}|0|EN',
                )
            )

        keyboard.row(
            InlineKeyboardButton(text="⬅️", callback_data="go-to-top|0|EN"),
            InlineKeyboardButton(text="❌", callback_data="delete-message"),
            InlineKeyboardButton(text="➡️", callback_data="go-to-top|2|EN"),
        )
        await msg.answer(
            text=await LangSet(user_id).get_translation("top"), reply_markup=keyboard
        )


@dp.callback_query_handler(text_startswith="go-to-top", state="*")
async def go_to_top_callback(call: CallbackQuery):
    infolist = call.data.split("|")
    user_id = call.from_user.id
    language = infolist[2]
    page = int(infolist[1])
    if page == 0:
        try:
            await call.answer(
                text=await LangSet(user_id).get_translation("YOURE_ST_PAGE"),
                show_alert=False,
            )
        except:
            pass
    else:
        get_musics = await db.select_all_tops(
            limit=10, country=language, offset=10 * (page - 1)
        )
        if not get_musics:
            try:
                await call.answer(
                    text=await LangSet(user_id).get_translation("YOURE_LAST_PAGE"),
                    show_alert=False,
                )
            except:
                pass
        else:
            countrys = await top_chart_country(code=language)
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.row(*countrys)
            for music in get_musics:
                keyboard.add(
                    InlineKeyboardButton(
                        text=music["title"],
                        callback_data=f'get-top-music|{music["music_id"]}|{page}|{language}',
                    )
                )

            keyboard.row(
                InlineKeyboardButton(
                    text="⬅️", callback_data=f"go-to-top|{page - 1}|{language}"
                ),
                InlineKeyboardButton(text="❌", callback_data="delete-message"),
                InlineKeyboardButton(
                    text="➡️", callback_data=f"go-to-top|{page + 1}|{language}"
                ),
            )
            try:
                await call.message.edit_reply_markup(reply_markup=keyboard)
            except:
                pass


@dp.callback_query_handler(text_startswith="get-country-", state="*")
async def go_to_top_callback(call: CallbackQuery):
    language = call.data.replace("get-country-", "")
    countrys = await top_chart_country(code=language)
    top_tracks = await db.select_all_tops(country=language, limit=10)
    if top_tracks:
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.row(*countrys)
        for i, music in enumerate(top_tracks):
            keyboard.add(
                InlineKeyboardButton(
                    text=music["title"],
                    callback_data=f'get-top-music|{music["music_id"]}|0|{language}',
                )
            )

        keyboard.row(
            InlineKeyboardButton(text="⬅️", callback_data=f"go-to-top|0|{language}"),
            InlineKeyboardButton(text="❌", callback_data="delete-message"),
            InlineKeyboardButton(text="➡️", callback_data=f"go-to-top|2|{language}"),
        )
        await call.message.edit_reply_markup(reply_markup=keyboard)
    else:
        countrys = await top_chart_country(code="EN")
        top_tracks = await db.select_all_tops(country="EN", limit=10)
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.row(*countrys)
        for i, music in enumerate(top_tracks):
            keyboard.add(
                InlineKeyboardButton(
                    text=music["title"],
                    callback_data=f'get-top-music|{music["music_id"]}|0|EN',
                )
            )

        keyboard.row(
            InlineKeyboardButton(text="⬅️", callback_data="go-to-top|0|EN"),
            InlineKeyboardButton(text="❌", callback_data="delete-message"),
            InlineKeyboardButton(text="➡️", callback_data="go-to-top|2|EN"),
        )
        await call.message.edit_reply_markup(reply_markup=keyboard)


@dp.callback_query_handler(text_startswith="get-top-music", state="*")
async def go_to_top_callback(call: CallbackQuery):
    infolist = call.data.split("|")
    page = infolist[2]
    music_id = infolist[1]
    language = infolist[3]
    user_id = call.from_user.id
    title = await db.select_tops(music_id=music_id)
    keyboard = InlineKeyboardMarkup(row_width=5)
    searched_musics = await SearchMusic.search_music(
        query=title["title"], limit=5, ignore_results=True
    )
    if searched_musics:
        caption = "<b>🎧 " + title["title"] + "</b>\n\n"
        for i, music in enumerate(searched_musics):
            k = InlineKeyboardButton(
                text=str(i + 1), callback_data=f'download-music-{music["music_id"]}'
            )
            caption += f"{i + 1}. <i>{music['title']}</i>\n"

            if i == 0:
                keyboard.add(k)
            else:
                keyboard.insert(k)

        keyboard.row(
            InlineKeyboardButton(
                text=await LangSet(user_id).get_translation("back_top"),
                callback_data=f"back_top|{language}|{page}",
            )
        )
        try:
            await call.message.edit_text(text=caption, reply_markup=keyboard)
        except:
            pass
    else:
        try:
            bots_answer = await call.message.answer(
                await LangSet(user_id).get_translation("ERROR_MESSAGE"), reply=True
            )
        except:
            pass


@dp.callback_query_handler(text_startswith="back_top", state="*")
async def go_to_top_callback(call: CallbackQuery):
    infolist = call.data.split("|")
    user_id = call.from_user.id
    language = infolist[1]
    page = int(infolist[2])
    if page == 0:
        k = 0
    else:
        k = 10 * (page - 1)
    get_musics = await db.select_all_tops(limit=10, country=language, offset=k)
    countrys = await top_chart_country(code=language)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.row(*countrys)
    for music in get_musics:
        keyboard.add(
            InlineKeyboardButton(
                text=music["title"],
                callback_data=f'get-top-music|{music["music_id"]}|{page}|{language}',
            )
        )

    keyboard.row(
        InlineKeyboardButton(
            text="⬅️",
            callback_data=f"go-to-top|{0 if page == 0 else page - 1}|{language}",
        ),
        InlineKeyboardButton(text="❌", callback_data="delete-message"),
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"go-to-top|{2 if page == 0 else page + 1}|{language}",
        ),
    )
    try:
        await call.message.edit_text(
            text=await LangSet(user_id).get_translation("top"), reply_markup=keyboard
        )
    except:
        pass


@dp.callback_query_handler(text_startswith="delete-message", state="*")
async def go_to_top_callback(call: CallbackQuery):
    await call.answer("✅")
    await call.message.delete()
