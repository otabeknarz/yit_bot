from json import loads

from keyboards.inline.menu import add_keyboard
from loader import db, bot


async def referral_checker(text: str):
    if text != "/start":
        if "/start" in text:
            referral_link = text.replace("/start ", "").strip()
            result = await db.select_referal(code=referral_link)

            if not result:
                await db.add_referals(code=referral_link)
            else:
                members = result["members"] + 1
                days = result["days"] + 1
                weekly = result["weekly"] + 1
                await db.update_referals_member(
                    days=days, weekly=weekly, members=members, code=referral_link
                )


async def media_checker(text: str, user_id):
    if text != "/start":
        referral_link = text.replace("/start ", "").strip()
        result = await db.select_post(code=referral_link)
        if result:
            if result["content"] == "photo":
                await bot.send_photo(
                    chat_id=user_id,
                    photo=result["file_id"],
                    caption=None if result["caption"] == "None" else result["caption"],
                    reply_markup=await add_keyboard(user_id),
                )
                ...
            elif result["content"] == "voice":
                await bot.send_voice(
                    chat_id=user_id,
                    voice=result["file_id"],
                    caption=None if result["caption"] == "None" else result["caption"],
                    reply_markup=await add_keyboard(user_id),
                )
            elif result["content"] == "text":
                await bot.send_message(
                    chat_id=user_id,
                    text=None if result["caption"] == "None" else result["caption"],
                    reply_markup=await add_keyboard(user_id),
                )
            elif result["content"] == "sticker":
                await bot.send_sticker(
                    chat_id=user_id,
                    sticker=result["file_id"],
                    reply_markup=await add_keyboard(user_id),
                )
            elif result["content"] == "animation":
                await bot.send_animation(
                    chat_id=user_id,
                    animation=result["file_id"],
                    caption=None if result["caption"] == "None" else result["caption"],
                    reply_markup=await add_keyboard(user_id),
                )
            elif result["content"] == "video_note":
                await bot.send_video_note(
                    chat_id=user_id,
                    video_note=result["file_id"],
                    caption=None if result["caption"] == "None" else result["caption"],
                    reply_markup=await add_keyboard(user_id),
                )
            elif result["content"] == "audio":
                await bot.send_audio(
                    chat_id=user_id,
                    audio=result["file_id"],
                    caption=None if result["caption"] == "None" else result["caption"],
                    reply_markup=await add_keyboard(user_id),
                )
            elif result["content"] == "video":
                await bot.send_video(
                    chat_id=user_id,
                    video=result["file_id"],
                    caption=None if result["caption"] == "None" else result["caption"],
                    reply_markup=await add_keyboard(user_id),
                )


async def ads_checker(user_id):

    result = await db.select_sps()
    if result:
        if result["reply_markup"]:
            reply_markup = loads(result["reply_markup"])
        else:
            reply_markup = None
        if result["content"] == "photo":
            await bot.send_photo(
                chat_id=user_id,
                photo=result["file_id"],
                caption=None if result["caption"] == "None" else result["caption"],
                reply_markup=reply_markup,
            )
            ...
        elif result["content"] == "voice":
            await bot.send_voice(
                chat_id=user_id,
                voice=result["file_id"],
                caption=None if result["caption"] == "None" else result["caption"],
                reply_markup=reply_markup,
            )
        elif result["content"] == "text":
            await bot.send_message(
                chat_id=user_id,
                text=None if result["caption"] == "None" else result["caption"],
                reply_markup=reply_markup,
            )
        elif result["content"] == "sticker":
            await bot.send_sticker(
                chat_id=user_id, sticker=result["file_id"], reply_markup=reply_markup
            )
        elif result["content"] == "animation":
            await bot.send_animation(
                chat_id=user_id,
                animation=result["file_id"],
                caption=None if result["caption"] == "None" else result["caption"],
                reply_markup=reply_markup,
            )
        elif result["content"] == "video_note":
            await bot.send_video_note(
                chat_id=user_id,
                video_note=result["file_id"],
                caption=None if result["caption"] == "None" else result["caption"],
                reply_markup=reply_markup,
            )
        elif result["content"] == "audio":
            await bot.send_audio(
                chat_id=user_id,
                audio=result["file_id"],
                caption=None if result["caption"] == "None" else result["caption"],
                reply_markup=reply_markup,
            )
        elif result["content"] == "video":
            await bot.send_video(
                chat_id=user_id,
                video=result["file_id"],
                caption=None if result["caption"] == "None" else result["caption"],
                reply_markup=reply_markup,
            )
