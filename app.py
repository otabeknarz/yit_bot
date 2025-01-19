from aiogram import executor, types

from loader import dp, db
import middlewares
import filters, handlers
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands


async def on_startup(dispatcher):
    await db.create()
    # await db.drop_all_tables()
    await db.create_table_users()
    await db.create_table_sps()
    await db.create_table_groups()
    await db.create_table_settings()
    await db.create_table_audios()
    await db.create_table_referals()
    await db.create_table_admins()
    await db.create_table_medias()
    await db.create_table_bots()
    await db.create_table_ads()
    await db.create_table_posts()
    await db.create_table_tops()
    await db.create_table_channels()
    await db.create_table_join_requests()
    await db.create_table_mailing()
    check = await db.select_settings()
    if not check:
        await db.add_settings()
    # Birlamchi komandalar (/star va /help)
    await set_default_commands(dispatcher)

    # Bot ishga tushgani haqida adminga xabar berish
    await on_startup_notify(dispatcher)


if __name__ == "__main__":
    executor.start_polling(
        dp,
        on_startup=on_startup,
        skip_updates=True,
    )
