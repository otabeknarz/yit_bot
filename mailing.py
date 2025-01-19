import asyncio
import json
import logging
from datetime import datetime

from aiogram.utils import exceptions

from libs.AdminsList import admins_list
from loader import bot, db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("broadcast")


async def send_message(
    chat_id, user_id, message_id, reply_markup=None, mail_type="oddiy"
) -> bool:
    try:
        if mail_type == "oddiy":
            if reply_markup:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=reply_markup,
                )
            else:

                await bot.copy_message(
                    chat_id=user_id, from_chat_id=chat_id, message_id=message_id
                )
        elif mail_type == "forward":
            await bot.forward_message(
                chat_id=user_id, from_chat_id=chat_id, message_id=message_id
            )
    except exceptions.BotBlocked:
        log.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(
            f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds."
        )
        await asyncio.sleep(e.timeout)
        return await send_message(
            chat_id, user_id, message_id, reply_markup, mail_type
        )  # Recursive call
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        log.exception(f"Target [ID:{user_id}]: failed")

    else:
        log.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def mailingRun():
    await db.create()
    log.info(f"Mailing started" + str(datetime.now()))
    run = True
    while run:
        try:
            sts = await db.select_mailing()
            res = dict(sts)
        except Exception as e:
            log.error(e)
            res = None

        if not res:
            await asyncio.sleep(2)
            continue
        if not res["status"]:
            await asyncio.sleep(2)
            continue
        if res["status"]:
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
            not_send, send = not_send, send
            if reply_markup:
                reply_markup = json.loads(reply_markup)

            if type == "users":
                table = "users"
                if location == "all":
                    user = await db.select_users_mailing(offset=offset)
                else:
                    user = await db.select_users_location_mailing(
                        offset=offset, location=location
                    )
            if type == "groups":
                table = "groups"
                user = await db.select_groups_mailing(offset=offset)

            if not user:
                await db.update_mailing_status(status=False, id=id)
                ADMINS = await admins_list()
                for admin in ADMINS:
                    try:
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
                        await bot.send_message(
                            admin,
                            f"<b>Habar yuborish tugadi\n\n✅ Yuborilgan: <code>{send}</code>\n❌ Yuborilmagan: <code>{not_send}</code> \n\n📅 Habar yuborish uchun sarflangan vaqt:</b> <code>{duration}</code>",
                        )
                    except Exception as e:
                        log.error(e)
                        pass
                run = False
                continue
            else:
                for x in user:
                    await asyncio.sleep(0.05)
                    send_post_result = await send_message(
                        chat_id=user_id,
                        user_id=x["user_id"],
                        message_id=message_id,
                        reply_markup=reply_markup,
                        mail_type=mail_type,
                    )

                    if send_post_result:
                        send += 1
                    else:
                        not_send += 1
                        await db.update_mailling_table_status(
                            table=table, status="passive", user_id=x["user_id"]
                        )

                    await db.update_mailing_results(
                        send=send, not_send=not_send, offset=x["id"], id=id
                    )


if __name__ == "__main__":
    asyncio.run(mailingRun())
