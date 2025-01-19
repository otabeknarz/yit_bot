import asyncio
import time
from os import listdir, stat

from aiofiles.os import remove
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from data.config import MEDIA_DIRECTORY
from loader import db


async def update_scheduler():
    files = listdir(MEDIA_DIRECTORY)

    for file in files:
        if file == "thumbnail-original.jpg" or file == "thumbnail.jpg":
            continue

        timedelta = time.time() - stat(MEDIA_DIRECTORY + file).st_ctime
        if timedelta > 600:
            await remove(MEDIA_DIRECTORY + file)
    await db.create()
    await db.update_link_members()


async def weekly_scheduler():
    await db.create()
    await db.update_link_members_weekly()


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_scheduler, "cron", hour=0, minute=3)
    scheduler.add_job(weekly_scheduler, "cron", day_of_week="mon", hour=0, minute=3)

    scheduler.start()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
