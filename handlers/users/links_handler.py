import asyncio
import logging
import urllib.parse
import logging

from aiofiles import os
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import CancelHandler
from aiogram.types import ChatType, MediaGroup, input_file
from aiogram.utils.exceptions import RetryAfter

from data.config import MEDIA_DIRECTORY
from keyboards.inline.menu import add_keyboard, search_keyboard
from libs.downloads_manager import VideoDownloader
from libs.url_checker import LinksChecker
from loader import dp, bot, db
from states.state import searching_states
from utils.check_channel import check_channel
from utils.language import LangSet

logger = logging.getLogger(__name__)


@dp.message_handler(
    lambda msg: "tiktok.com" in msg.text
    or "pin.it" in msg.text
    or "pinterest.com" in msg.text
    or "likee.video" in msg.text
    or "youtu.be" in msg.text
    or "youtube.com" in msg.text
    or "instagram.com" in msg.text,
    content_types=["text"],
    state="*",
)
async def links_finder_handler(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    bot_ = await bot.get_me()
    BOTNAME = f"@{bot_.username}"

    if msg.chat.type in ["group", "supergroup"]:
        check_user = await db.select_group(user_id=int(msg.chat.id))
        if not check_user:
            try:
                await db.add_group(user_id=int(msg.chat.id))
            except Exception as err:
                logging.error(err)

    if msg.chat.type == "private":
        check = await db.select_settings()
        if check["value"] == "True":
            check = await check_channel(user_id)
            if check:
                await msg.delete()
                text, keyboard = check
                await msg.answer(text=text, reply_markup=keyboard)
                raise CancelHandler()

    if msg.chat.type == "private":
        if await state.get_state() == searching_states.searching_details.state:
            try:
                async with state.proxy() as data:
                    if data.get("bots_answer") is not None:
                        await bot.delete_message(
                            chat_id=msg.from_user.id, message_id=data["bots_answer"]
                        )
                    if data.get("users_message") is not None:
                        await bot.delete_message(
                            chat_id=msg.from_user.id,
                            message_id=data.get("users_message"),
                        )
            except Exception as e:
                logger.error(e)

    bots_answer = None
    links_checker = LinksChecker(msg.text)
    if "tiktok.com" in msg.text:
        link = links_checker.get_tiktok_link()
    elif "pin.it" in msg.text or "pinterest.com" in msg.text:
        link = links_checker.get_pinterest_link()
    elif "likee.video" in msg.text:
        link = links_checker.get_likee_link()
    elif "youtu.be" in msg.text or "youtube.com" in msg.text:
        link = links_checker.get_youtube_link()
    elif "instagram.com" in msg.text:
        parsed_url = urllib.parse.urlparse(links_checker.get_instagram_link())
        link = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
    else:
        link = None

    if link is None:
        if msg.chat.type == "private":
            try:
                bots_answer = await msg.reply(
                    await LangSet(user_id).get_translation("LINK_ERROR_MESSAGE")
                )
            except Exception as e:
                logging.error(e)
    else:
        try:
            if msg.chat.type == "private":
                downloading_message = await msg.answer("⏳")
            else:
                downloading_message = None
        except Exception as e:
            logging.error(e)
            downloading_message = None
        txt_m = await LangSet(user_id).get_translation("VIDEO_DOWNLOADED_MESSAGE")

        if "instagram.com" in msg.text:
            insta_check = await db.select_all_medias(link=link)
            if insta_check:
                if len(insta_check) == 1:
                    try:
                        await msg.answer_video(
                            video=insta_check[0]["file_id"],
                            caption=txt_m.replace("*bot", BOTNAME),
                            reply_markup=await search_keyboard(user_id),
                        )
                    except Exception as e:
                        await msg.answer_photo(
                            photo=insta_check[0]["file_id"],
                            caption=txt_m.replace("*bot", BOTNAME),
                            reply_markup=await add_keyboard(user_id),
                        )

                    except Exception as e:
                        logging.error(e)
                else:
                    input_medias = MediaGroup()
                    for i, x in enumerate(insta_check):
                        res = await msg.bot.get_file(x["file_id"])
                        file_path = res.file_path
                        if "photos" in file_path:
                            input_medias.attach_photo(
                                photo=res.file_id,
                                caption=(
                                    txt_m.replace("*bot", BOTNAME) if i == 0 else None
                                ),
                            )

                        elif "videos" in file_path:
                            input_medias.attach_video(
                                video=res.file_id,
                                caption=(
                                    txt_m.replace("*bot", BOTNAME) if i == 0 else None
                                ),
                            )
                    await msg.answer_media_group(media=input_medias)
                if downloading_message is not None:
                    await downloading_message.delete()
                return
        check_video = await db.select_media(link=link)
        if check_video:
            if check_video["content"] == "animation":
                try:
                    await msg.answer_animation(
                        animation=check_video["file_id"],
                        caption=txt_m.replace("*bot", BOTNAME),
                        reply_markup=await add_keyboard(user_id),
                    )
                except:
                    pass
            else:
                try:
                    await msg.answer_video(
                        video=check_video["file_id"],
                        caption=txt_m.replace("*bot", BOTNAME),
                        reply_markup=await search_keyboard(user_id),
                    )

                except RetryAfter as e:
                    await asyncio.sleep(e.timeout)
                    await msg.answer_video(
                        video=check_video["file_id"],
                        caption=txt_m.replace("*bot", BOTNAME),
                        reply_markup=await search_keyboard(user_id),
                    )
                except Exception as e:
                    logger.error(e)
                    await msg.answer_photo(
                        photo=check_video["file_id"],
                        caption=txt_m.replace("*bot", BOTNAME),
                        reply_markup=await add_keyboard(user_id),
                    )
        else:
            upload_status = True  # Videolarni yuklab olish uchun status
            video_downloader = VideoDownloader(
                video_url=link,
                user_id=MEDIA_DIRECTORY + str(msg.chat.id) + "-" + str(msg.message_id),
                upload=upload_status,
            )
            downloaded_video_details = await video_downloader.final_download()
            if downloaded_video_details["instagram"]:
                input_medias = MediaGroup()
                remove_list = []
                if len(downloaded_video_details["results"]) == 1:
                    remove_list.append(downloaded_video_details["results"][0]["path"])
                    if downloaded_video_details["results"][0]["type"] == "image":
                        try:
                            photo_file = await msg.answer_photo(
                                photo=input_file.InputFile(
                                    downloaded_video_details["results"][0]["path"]
                                ),
                                caption=txt_m.replace("*bot", BOTNAME),
                                reply_markup=await add_keyboard(user_id),
                            )
                            file_id = photo_file.photo[-1].file_id
                            try:
                                await db.add_medias(
                                    link=link, file_id=file_id, content="photo"
                                )
                            except:
                                pass
                        except Exception as e:
                            logging.error(e)
                    elif downloaded_video_details["results"][0]["type"] == "video":
                        try:
                            video_file = await msg.answer_video(
                                video=input_file.InputFile(
                                    downloaded_video_details["results"][0]["path"]
                                ),
                                caption=txt_m.replace("*bot", BOTNAME),
                                duration=downloaded_video_details["results"][0]["duration"],
                                width=downloaded_video_details["results"][0]["width"],
                                height=downloaded_video_details["results"][0]["height"],
                                reply_markup=await search_keyboard(user_id),
                            )
                            remove_list.append(downloaded_video_details["results"][0]["thumb"])
                            file_id = video_file.video.file_id
                            try:
                                await db.add_medias(link=link, file_id=file_id)
                            except:
                                pass
                        except Exception as e:
                            logging.error(e)
                else:
                    for i, x in enumerate(downloaded_video_details["results"]):
                        remove_list.append(x["path"])
                        if x["type"] == "image":
                            input_medias.attach_photo(
                                photo=input_file.InputFile(path_or_bytesio=x["path"]),
                                caption=(
                                    txt_m.replace("*bot", BOTNAME) if i == 0 else None
                                ),
                            )
                        elif x["type"] == "video":
                            input_medias.attach_video(
                                video=input_file.InputFile(path_or_bytesio=x["path"]),
                                caption=(
                                    txt_m.replace("*bot", BOTNAME) if i == 0 else None
                                ),
                            )
                    try:
                        test = await msg.answer_media_group(media=input_medias)
                        for r in test:
                            if r.photo:
                                file_id = r.photo[-1].file_id
                                try:
                                    await db.add_medias(
                                        link=link, file_id=file_id, content="photo"
                                    )
                                except:
                                    pass
                            elif r.video:
                                file_id = r.video.file_id
                                try:
                                    await db.add_medias(link=link, file_id=file_id)
                                except:
                                    pass

                    except Exception as e:
                        pass
                for file_path in remove_list:
                    try:
                        await os.remove(file_path)
                    except Exception as e:
                        print(f"Error while removing file: {e}")
            elif downloaded_video_details["ok"]:

                if downloaded_video_details["type"] in ["image/gif", "video"]:
                    if downloaded_video_details["type"] == "video":
                        try:
                            video_file = await msg.answer_video(
                                video=input_file.InputFile(
                                    path_or_bytesio=downloaded_video_details["path"]
                                ),
                                width=downloaded_video_details["width"],
                                height=downloaded_video_details["height"],
                                duration=downloaded_video_details["duration"],
                                caption=txt_m.replace("*bot", BOTNAME),
                                reply_markup=await search_keyboard(user_id),
                            )
                            file_id = video_file.video.file_id
                        except RetryAfter as e:
                            await asyncio.sleep(e.timeout)
                            video_file = await msg.answer_video(
                                video=input_file.InputFile(
                                    path_or_bytesio=downloaded_video_details["path"]
                                ),
                                width=downloaded_video_details["width"],
                                height=downloaded_video_details["height"],
                                duration=downloaded_video_details["duration"],
                                caption=txt_m.replace("*bot", BOTNAME),
                                reply_markup=await search_keyboard(user_id),
                            )
                            file_id = video_file.video.file_id
                        except Exception as e:
                            logging.error(e)
                            file_id = None
                        if file_id is not None:
                            try:
                                await db.add_medias(link=link, file_id=file_id)
                            except Exception as e:
                                logger.error(e)

                    elif downloaded_video_details["type"] == "image/gif":
                        try:
                            animation = await msg.answer_animation(
                                animation=input_file.InputFile(
                                    path_or_bytesio=downloaded_video_details["path"]
                                ),
                                caption=txt_m.replace("*bot", BOTNAME),
                                reply_markup=await add_keyboard(user_id),
                            )
                            file_id = animation.document.file_id
                        except Exception as e:
                            logger.error(e)
                            file_id = None
                        if file_id is not None:
                            try:
                                await db.add_medias(
                                    link=link, file_id=file_id, content="animation"
                                )
                            except Exception as e:
                                logger.error(e)
                else:
                    try:
                        send_photo = await msg.answer_photo(
                            photo=input_file.InputFile(
                                path_or_bytesio=downloaded_video_details["path"]
                            ),
                            caption=txt_m.replace("*bot", BOTNAME),
                            reply_markup=await add_keyboard(user_id),
                        )
                        file_id = send_photo.photo[-1].file_id
                    except Exception as e:
                        logger.error(e)
                        file_id = None
                    if file_id is not None:
                        try:
                            await db.add_medias(
                                link=link, file_id=file_id, content="photo"
                            )
                        except Exception as e:
                            logger.error(e)

            elif downloaded_video_details["status"] == "SUCCESS":
                try:
                    video_file = await msg.answer_video(
                        video=input_file.InputFile(
                            path_or_bytesio=downloaded_video_details["path"]
                        ),
                        caption=txt_m.replace("*bot", BOTNAME),
                        duration=downloaded_video_details["duration"],
                        width=downloaded_video_details["width"],
                        height=downloaded_video_details["height"],
                        reply_markup=await search_keyboard(user_id),
                    )
                    file_id = video_file.video.file_id
                except RetryAfter as e:
                    await asyncio.sleep(e.timeout)
                    video_file = await msg.answer_video(
                        video=input_file.InputFile(
                            path_or_bytesio=downloaded_video_details["path"]
                        ),
                        caption=txt_m.replace("*bot", BOTNAME),
                        duration=downloaded_video_details["duration"],
                        width=downloaded_video_details["width"],
                        height=downloaded_video_details["height"],
                        reply_markup=await search_keyboard(user_id),
                    )
                    file_id = video_file.video.file_id
                except Exception as e:
                    logging.error(e)
                    file_id = None
                if file_id is not None:
                    try:
                        await db.add_medias(link=link, file_id=file_id)
                    except Exception as e:
                        logger.error(e)

            else:
                if msg.chat.type == "private":
                    if video_downloader.error == "file-is-too-big":
                        text = await LangSet(user_id).get_translation(
                            "FILE_IS_TOO_BIG_MESSAGE"
                        )
                    elif video_downloader.error == "link-is-not-supported":
                        text = await LangSet(user_id).get_translation(
                            "LINK_IS_NOT_SUPPORTED"
                        )
                    else:
                        txt = await LangSet(user_id).get_translation(
                            "DOWNLOAD_ERROR_MESSAGE"
                        )
                        text = txt.replace("*link", link)

                    try:
                        bots_answer = await msg.reply(text)
                    except Exception as e:
                        pass
        if downloading_message is not None:
            await downloading_message.delete()
    if msg.chat.type == "private":
        await searching_states.searching_details.set()
        async with state.proxy() as date:
            date["bots_answer"] = (
                bots_answer.message_id if bots_answer is not None else None
            )
            date["users_message"] = msg.message_id

    try:
        await os.remove(
            MEDIA_DIRECTORY + str(msg.chat.id) + "-" + str(msg.message_id) + ".mp4"
        )
    except Exception as e:
        pass
    try:
        await os.remove(
            MEDIA_DIRECTORY + str(msg.chat.id) + "-" + str(msg.message_id) + ".jpg"
        )
    except Exception as e:
        pass
    try:
        await os.remove(
            MEDIA_DIRECTORY + str(msg.chat.id) + "-" + str(msg.message_id) + ".gif"
        )
    except Exception as e:
        pass
