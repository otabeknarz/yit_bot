import pprint

import youtubesearchpython
from aiofiles import os
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import CancelHandler
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputFile,
)
import yt_dlp

from keyboards.inline.menu import add_keyboard
from libs.SyncToAsync import ToAsync
from libs.download_music import SearchMusic, Music
from loader import dp, bot, db
from states.state import searching_states
from utils.check_channel import check_channel
from utils.language import LangSet
import logging
import aiohttp


logger = logging.getLogger(__name__)


@ToAsync()
def search_yt_dlp(query: str, limit: int = 15, duration_limit: int = 900) -> list[dict]:
    """
    Searches for videos on YouTube using yt-dlp.

    Arguments:
        query (str): The search query.
        limit (int): The maximum number of videos to return (default 15).
        duration_limit (int): The maximum duration of the video in seconds (default 900).
    Returns:
        list[dict]: A list of dictionaries containing the video information.
    """

    # yt-dlp options for searching no to download the video
    search_yt_dlp_options = {
        "cookiefile": "www.youtube.com_cookies.txt",
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
        "extract_flat": True,
    }

    # Search for videos on YouTube and extract the information
    with yt_dlp.YoutubeDL(search_yt_dlp_options) as ydl:
        search_query = f"ytsearch{limit}:{query}"
        search_results = ydl.extract_info(search_query, download=False)

    # List to store the extracted video information
    videos: list[dict] = []

    # Extract video information if the nothing found in the
    # search results the function returns an empty list
    for entry in search_results.get("entries", []):
        if entry is not None:
            (
                videos.append(
                    {
                        "title": entry.get("title"),
                        "url": entry.get("url"),
                        "music_id": entry.get("id"),
                        "duration": entry.get("duration"),
                        "thumbnail": (
                            entry.get("thumbnails")[
                                len(entry.get("thumbnails")) - 1
                            ].get("url")
                            if entry.get("thumbnails")
                            and len(entry.get("thumbnails")) > 0
                            else None
                        ),
                    }
                )
                if entry.get("duration") <= duration_limit
                else None
            )

    return videos


class YouTubeVideoCategories:
    film = 1
    autos = 2
    music = 10
    animals = 15
    sports = 17
    travel = 19
    games = 20
    people = 22
    comedy = 23
    entertainment = 24
    news = 25
    howto = 26
    education = 27
    science = 28
    tech = 30


async def manual_search(
    query: str,
    limit: int = 10,
    page_token: str = "",
    category_type: int = 10,
) -> tuple[list[dict], str, str]:
    """
    Searches for videos on YouTube not using any library with just an api of the YouTube.

    Arguments:
        query (str): The search query.
        limit (int): The maximum number of videos to return (default 15).
        page_token (str): The page token to get the next page of the search results (default "").
        category_type (int): The category type of the video (default 10).

    Returns:
        tuple(list[dict], str, str): A tuple containing the list of videos, previous page token and next page token.
    """

    youtube_search_api_base_url = "https://www.googleapis.com/youtube/v3/search"

    search_params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": limit,
        "videoCategoryId": category_type,
        "key": "AIzaSyBIkyh3b9zePuimQbghqRtSZIXwiqlVyQI",  # AIzaSyD-3Q7Q5t8h9Vv3lJ6JjBwRd1wDvZyZ1qA
        "pageToken": page_token,
    }

    prev_page_token: str = ""
    next_page_token: str = ""
    videos: list[dict] = []

    async with aiohttp.ClientSession() as session:
        # Making the async request with aiohttp
        response = await session.get(youtube_search_api_base_url, params=search_params)
        # Convert the response to python dict from json type
        json_response = await response.json()
        # Assigning prev and next page token if it exists
        prev_page_token = json_response.get("prevPageToken")
        next_page_token = json_response.get("nextPageToken")
        # Extracting each video details from the response
        for item in json_response.get("items", []):
            # Collecting video details into one dict
            video_details = {
                "id": item.get("id", {}).get("videoId"),
                "title": item.get("snippet", {}).get("title"),
                "channel": item.get("snippet", {}).get("channelTitle"),
                "thumbnail": item.get("snippet", {})
                .get("thumbnails", {})
                .get("medium", {})
                .get("url"),
            }
            # Adding the video details to the videos list
            videos.append(video_details)

    return videos, prev_page_token, next_page_token


@dp.message_handler(content_types=["text"], state="*")
async def search_music_main(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    try:
        searching_message = await msg.answer(text="🔎")
    except Exception as e:
        logger.error(e)
        searching_message = None

    try:
        # Checking for every state if there is any message to delete
        async with state.proxy() as data:
            for _ in ("bots_answer", "music_info_message", "users_message"):
                if data.get(_) is not None:
                    await dp.bot.delete_message(
                        chat_id=msg.from_user.id, message_id=data[_]
                    )

    except Exception as e:
        logger.error(e)

    await state.finish()

    manual_searched_musics, prev_page_token, next_page_token = await manual_search(
        msg.text
    )

    # Checking if the search results are not empty
    if len(manual_searched_musics) > 0:
        message = await LangSet(user_id).get_translation("SEARCH_STATS") + "\n\n"
        keyboard = InlineKeyboardMarkup(row_width=5)
        for key, music in enumerate(manual_searched_musics, start=1):
            message += f"{key}. <i>{music.get('title')}</i>\n"
            keyboard.insert(
                InlineKeyboardButton(
                    text=str(key), callback_data=f'download-music-{music.get("id")}'
                )
            )

        keyboard.add(
            InlineKeyboardButton(text="⬅️", callback_data="go-to-page-0"),
            InlineKeyboardButton(text="❌", callback_data="delete-message"),
            InlineKeyboardButton(text="➡️", callback_data=f"go-to-next-page-{next_page_token}"),
        )

        try:
            bots_answer = await msg.answer(text=message, reply_markup=keyboard)
        except Exception as e:
            logger.error(e)
            bots_answer = None

        if searching_message is not None:
            await searching_message.delete()
        await searching_states.searching_details.set()
        async with state.proxy() as data:
            data["search_query"] = msg.text
            data["bots_answer"] = bots_answer.message_id
            data["users_message"] = msg.message_id

    else:
        if searching_message is not None:
            await searching_message.edit_text(
                text=await LangSet(user_id).get_translation("MUSIC_NOT_FINDED_MESSAGE"),
                reply_markup=await add_keyboard(user_id),
            )


@dp.callback_query_handler(
    text_startswith="go-to-next-page",
    state=searching_states.searching_details,
)
async def go_to_page_callback(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    page_token = call.data.replace("go-to-next-page-", "")

    if page_token == "last":
        try:
            await call.answer(await LangSet(user_id).get_translation("YOURE_LAST_PAGE"))
        except Exception as e:
            logger.error(e)
        return

    async with state.proxy() as data:
        search_query = data["search_query"]

    # page = 1
    manual_searched_musics, prev_page_token, next_page_token = await manual_search(
        search_query, page_token=page_token
    )

    if len(manual_searched_musics) > 0:
        message = await LangSet(user_id).get_translation("SEARCH_STATS") + "\n\n"
        keyboard = InlineKeyboardMarkup(row_width=5)

        for key, music in enumerate(manual_searched_musics, start=1):
            message += f"{key}. <i>{music.get('title')}</i>\n"
            keyboard.insert(
                InlineKeyboardButton(
                    text=str(key), callback_data=f'download-music-{music.get("id")}'
                )
            )

        keyboard.add(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"go-to-page-{prev_page_token if prev_page_token else 'first'}",
            ),
            InlineKeyboardButton(text="❌", callback_data="delete-message"),
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"go-to-next-page-{next_page_token if next_page_token else 'last'}",
            ),
        )

        try:
            await call.message.edit_text(text=message, reply_markup=keyboard)
        except Exception as e:
            logger.error(e)

    else:
        try:
            await call.answer(
                await LangSet(user_id).get_translation("YOURE_LAST_PAGE")
            )
        except Exception as e:
            logger.error(e)


@dp.callback_query_handler(
    text_startswith="go-to-page-",
    state=searching_states.searching_details,
)
async def go_to_page_callback(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    page_token = call.data.replace("go-to-page-", "")

    if page_token == "first":
        try:
            await call.answer(await LangSet(user_id).get_translation("YOURE_ST_PAGE"))
        except Exception as e:
            logger.error(e)
    else:
        async with state.proxy() as data:
            search_query = data["search_query"]

        manual_searched_musics, prev_page_token, next_page_token = await manual_search(
            search_query, page_token=page_token
        )

        message = await LangSet(user_id).get_translation("SEARCH_STATS") + "\n\n"
        keyboard = InlineKeyboardMarkup(row_width=5)

        for key, music in enumerate(manual_searched_musics, start=1):
            message += f"{key}. <i>{music.get('title')}</i>\n"
            keyboard.insert(
                InlineKeyboardButton(
                    text=str(key), callback_data=f'download-music-{music.get("id")}'
                )
            )

        keyboard.add(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"go-to-page-{prev_page_token if prev_page_token else 'first'}",
            ),
            InlineKeyboardButton(text="❌", callback_data="delete-message"),
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"go-to-next-page-{next_page_token if next_page_token else 'last'}",
            ),
        )

        try:
            await call.message.edit_text(text=message, reply_markup=keyboard)
        except Exception as e:
            logger.error(e)


@dp.callback_query_handler(text_startswith="download-music-", state="*")
async def go_to_top_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    bot_ = await bot.get_me()
    BOTNAME = f"@{bot_.username}"
    music_id = call.data.replace("download-music-", "")
    if call.message.chat.type == "private":
        check = await db.select_settings()
        if check["value"] == "True":
            check = await check_channel(user_id)
            if check:
                await call.message.delete()
                text, keyboard = check
                await call.message.answer(text=text, reply_markup=keyboard)
                raise CancelHandler()

    if call.message.chat.type == "private":
        try:
            await call.answer()
            bots_answer = await call.message.answer(
                text=await LangSet(user_id).get_translation("DOWNLOADING_MUSIC")
            )
        except:
            bots_answer = None
    else:
        await call.answer(
            text=await LangSet(user_id).get_translation("DOWNLOADING_MUSIC"),
            show_alert=True,
        )
        bots_answer = None
    try:
        txt_m = await LangSet(user_id).get_translation("VIDEO_DOWNLOADED_MESSAGE")
        check_db = await db.select_audio(music_id=music_id)

        if check_db:
            await call.answer()
            await call.message.answer_audio(
                audio=check_db["file_id"],
                caption=txt_m.replace("*bot", BOTNAME),
                reply_markup=await add_keyboard(user_id),
            )

        else:

            music_downloader = Music(
                music_id=music_id,
                file_path=f"downloaded_musics/{call.from_user.id}-{bots_answer.message_id if bots_answer is not None else 1}",
            )
            downloaded_music = await music_downloader.download_music()

            if downloaded_music["downloaded"]:

                try:
                    sended_audio = await call.message.answer_audio(
                        audio=InputFile(downloaded_music["audio-path"]),
                        title=downloaded_music["title"],
                        performer=BOTNAME,
                        duration=downloaded_music["audio-duration"],
                        caption=txt_m.replace("*bot", BOTNAME),
                        reply_markup=await add_keyboard(user_id),
                    )
                except Exception as e:
                    print("downloading audio error:", e)
                    sended_audio = None
                if sended_audio is not None:
                    try:
                        await db.add_audios(
                            title=downloaded_music["title"],
                            music_id=music_id,
                            file_id=sended_audio.audio.file_id,
                        )
                    except Exception as e:
                        pass

                try:
                    await os.remove(downloaded_music["audio-path"])
                except:
                    pass
            else:
                if call.message.chat.type == "private":
                    await call.message.answer(
                        await LangSet(user_id).get_translation("ERROR_MESSAGE")
                    )

        if bots_answer is not None:
            await bots_answer.delete()
    except Exception as e:
        print(e)
        if call.message.chat.type == "private":
            try:
                await call.message.answer(
                    await LangSet(user_id).get_translation("ERROR_MESSAGE")
                )
            except:
                pass
    if bots_answer is not None:
        try:
            await bots_answer.delete()
        except Exception as e:
            pass

    try:
        await os.remove(
            f"downloaded_musics/{call.from_user.id}-{bots_answer.message_id if bots_answer is not None else 1}.mp3"
        )
    except:
        pass
